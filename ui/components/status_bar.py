import time
import subprocess
import threading
import customtkinter as ctk
from config.settings import PALETTE, FONT_FAMILY
from utils.logger import AppLogger

logger = AppLogger("status_bar")

try:
    import psutil
except ImportError:
    psutil = None


class SystemStatusBar(ctk.CTkFrame):
    """Top application status / health bar with live CPU, RAM, battery, clock."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color=PALETTE["card_bg"], height=38, **kwargs)
        self.pack_propagate(False)
        self._build_ui()
        self._monitor_started = False

    def start_monitoring(self) -> None:
        """Start the background system monitor thread (call after mainloop starts)."""
        if self._monitor_started:
            return
        self._monitor_started = True
        self._start_monitor()

    def _build_ui(self) -> None:
        btn = ctk.CTkButton(
            self, text="⚡ SYSTEM MONITOR",
            font=("Consolas", 11, "bold"),
            fg_color="transparent",
            hover_color=PALETTE["card_hover"],
            text_color=PALETTE["accent"],
            anchor="w",
            width=140,
            height=28,
            command=self._open_task_manager,
        )
        btn.pack(side="left", padx=5)

        self.lbl_resources = ctk.CTkLabel(
            self, text="CPU: --% | RAM: --%",
            font=("Consolas", 11), text_color=PALETTE["text_sub"],
        )
        self.lbl_resources.pack(side="left", padx=15)

        self.lbl_clock = ctk.CTkLabel(
            self, text="--:--:--",
            font=("Consolas", 11, "bold"), text_color=PALETTE["text_main"],
        )
        self.lbl_clock.pack(side="right", padx=15)

        self.lbl_battery = ctk.CTkLabel(
            self, text="🔌 Power",
            font=("Consolas", 11), text_color=PALETTE["success"],
        )
        self.lbl_battery.pack(side="right", padx=10)

    def _open_task_manager(self) -> None:
        try:
            subprocess.Popen(["taskmgr.exe"])
        except Exception as exc:
            logger.error("Could not open Task Manager: %s", exc)

    def _start_monitor(self) -> None:
        def _loop() -> None:
            while True:
                ts = time.strftime("%H:%M:%S | %d/%m/%Y")
                res = "CPU: --% | RAM: --%"
                batt = "🔌 AC Power"

                if psutil:
                    cpu = psutil.cpu_percent(interval=None)
                    ram = psutil.virtual_memory().percent
                    res = f"CPU: {cpu:.1f}% | RAM: {ram:.1f}%"
                    battery = psutil.sensors_battery()
                    if battery:
                        prefix = "⚡ Charging" if battery.power_plugged else "🔋 Battery"
                        batt = f"{prefix}: {int(battery.percent)}%"

                try:
                    self.after(0, self._update_labels, ts, res, batt)
                except RuntimeError:
                    pass
                time.sleep(1.5)

        threading.Thread(target=_loop, daemon=True).start()

    def _update_labels(self, ts: str, res: str, batt: str) -> None:
        self.lbl_clock.configure(text=ts)
        self.lbl_resources.configure(text=res)
        self.lbl_battery.configure(text=batt)

    def update_theme(self, palette: dict) -> None:
        self.configure(fg_color=palette["card_bg"])
        self.lbl_resources.configure(text_color=palette["text_sub"])
        self.lbl_clock.configure(text_color=palette["text_main"])
        self.lbl_battery.configure(text_color=palette["success"])
