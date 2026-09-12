import sys
import os
import logging
import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Any


class UnbufferedStream:
    """Wraps a stream so that every write is flushed immediately.
    Safely handles None stream when running in --windowed mode.
    """

    def __init__(self, stream: Any) -> None:
        self.stream = stream

    def write(self, data: str) -> int:
        if self.stream is None:
            return 0
        result = self.stream.write(data)
        if hasattr(self.stream, 'flush'):
            self.stream.flush()
        return result

    def writelines(self, lines: Any) -> None:
        if self.stream is None:
            return
        self.stream.writelines(lines)
        if hasattr(self.stream, 'flush'):
            self.stream.flush()

    def __getattr__(self, attr: str) -> Any:
        if self.stream is None:
            return lambda *args, **kwargs: None
        return getattr(self.stream, attr)


def flush_streams() -> None:
    """Replace sys.stdout / sys.stderr with *unbuffered* variants."""
    if not isinstance(sys.stdout, UnbufferedStream):
        sys.stdout = UnbufferedStream(sys.stdout)
    if not isinstance(sys.stderr, UnbufferedStream):
        sys.stderr = UnbufferedStream(sys.stderr)


class AppLogger:
    """Centralised logger that writes to both console and a rolling log file.

    Usage::
        logger = AppLogger(__name__)
        logger.info("Vault scan started")
        logger.error("Permission denied on %s", path)
    """

    _instance: Optional["AppLogger"] = None
    _LOG_FILE: str = "app_debug.log"

    def __init__(self, name: str = "pentest_app", level: int = logging.DEBUG) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        # Đường dẫn thư mục log (tự động tạo thư mục nếu chưa tồn tại)
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / self._LOG_FILE

        # Console handler (Hiển thị INFO+)
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        self.logger.addHandler(console)

        # File handler với Rotating capability (DEBUG+) - max 5MB/file, lưu 3 file backup
        try:
            file_h = RotatingFileHandler(
                log_path,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
                delay=True,
            )
            file_h.setLevel(logging.DEBUG)
            file_h.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s [%(levelname)-7s] %(name)s:%(lineno)d — %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self.logger.addHandler(file_h)
        except Exception as e:
            sys.stderr.write(f"Failed to initialize file logger handler: {e}\n")

    # Pass-through methods
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.logger.exception(msg, *args, **kwargs)

    @staticmethod
    def get_timestamp() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")