"""Real-time system metrics engine using psutil.

Provides instantaneous CPU, RAM, disk, and network utilisation values
suitable for live dashboard gauges and charts.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    net_rx_bytes: float = 0.0
    net_tx_bytes: float = 0.0
    net_rx_mbps: float = 0.0
    net_tx_mbps: float = 0.0
    battery_percent: float = 0.0
    battery_charging: bool = False
    timestamp: float = field(default_factory=time.time)


class SystemMonitor:
    """Background thread that periodically samples system metrics.

    The latest :class:`SystemMetrics` instance is always available via
    the ``current`` property.  A rolling history of the last 60 samples
    is kept for chart rendering.
    """

    HISTORY_SIZE: int = 60
    SAMPLE_INTERVAL: float = 1.0

    def __init__(self, interval: float = SAMPLE_INTERVAL) -> None:
        self.interval = interval
        self._current: SystemMetrics = SystemMetrics()
        self._history: deque = deque(maxlen=self.HISTORY_SIZE)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._prev_net: tuple[float, float] | None = None
        self._prev_time: float | None = None

    @property
    def is_available(self) -> bool:
        return _PSUTIL_AVAILABLE

    @property
    def current(self) -> SystemMetrics:
        with self._lock:
            return self._current

    def get_history(self) -> list[SystemMetrics]:
        with self._lock:
            return list(self._history)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

    def _loop(self) -> None:
        while self._running:
            metrics = self._sample()
            with self._lock:
                self._current = metrics
                self._history.append(metrics)
            time.sleep(self.interval)

    def _sample(self) -> SystemMetrics:
        if not _PSUTIL_AVAILABLE:
            return SystemMetrics(timestamp=time.time())

        m = SystemMetrics(timestamp=time.time())
        # CPU
        m.cpu_percent = psutil.cpu_percent(interval=None)

        # RAM
        ram = psutil.virtual_memory()
        m.ram_percent = ram.percent
        m.ram_used_gb = ram.used / (1024 ** 3)
        m.ram_total_gb = ram.total / (1024 ** 3)

        # Disk
        try:
            disk = psutil.disk_usage("/")
            m.disk_percent = disk.percent
            m.disk_used_gb = disk.used / (1024 ** 3)
            m.disk_total_gb = disk.total / (1024 ** 3)
        except PermissionError:
            pass

        # Network
        net = psutil.net_io_counters()
        now = time.time()
        if self._prev_net and self._prev_time:
            dt = now - self._prev_time
            if dt > 0:
                rx_delta = net.bytes_recv - self._prev_net[0]
                tx_delta = net.bytes_sent - self._prev_net[1]
                m.net_rx_mbps = (rx_delta / (1024 ** 2)) / dt * 8
                m.net_tx_mbps = (tx_delta / (1024 ** 2)) / dt * 8
        self._prev_net = (net.bytes_recv, net.bytes_sent)
        self._prev_time = now
        m.net_rx_bytes = net.bytes_recv / (1024 ** 3)
        m.net_tx_bytes = net.bytes_sent / (1024 ** 3)

        # Battery
        try:
            battery = psutil.sensors_battery()
            if battery:
                m.battery_percent = battery.percent
                m.battery_charging = battery.power_plugged
        except Exception:
            pass

        return m
