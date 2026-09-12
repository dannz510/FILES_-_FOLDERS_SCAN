import os
import sys
import queue
import threading
import ctypes
import subprocess
from typing import Optional

from utils.logger import AppLogger

logger = AppLogger("pty_terminal")

# ---------------------------------------------------------------------------
# Windows PTY (Pseudo Console) support
# ---------------------------------------------------------------------------
# pywinpty provides a proper pseudo-console that:
#   • Preserves ANSI / VT escape sequences (colors, cursor movement)
#   • Fixes PSReadLine rendering issues
#   • Supports UTF-8 and autocompletion like VS Code
#   • Allows bidirectional piping of stdin / stdout
#
# On non-Windows platforms we fall back to a standard subprocess bridge.

try:
    from pty import openpty
    _PTY_AVAILABLE = sys.platform != "win32"
except ImportError:
    _PTY_AVAILABLE = False

if sys.platform == "win32":
    try:
        from winpty import PTY
        _WINPTY_AVAILABLE = True
    except ImportError:
        _WINPTY_AVAILABLE = False
        logger.warning("pywinpty not available; falling back to subprocess bridge")
else:
    _WINPTY_AVAILABLE = False


class PtyTerminalBridge:
    """Bidirectional terminal bridge using a pseudo-teletype.

    On Windows the ``pywinpty`` PTY implementation is used for full VT
    support.  On other platforms Python's stdlib ``pty`` module is used.
    If neither is available, a safe subprocess fallback is used.

    Output is streamed through an internal ``queue.Queue`` so the GUI can
    poll without blocking.
    """

    def __init__(self, command: str | list[str], is_admin: bool = False) -> None:
        self.command = command
        self.is_admin = is_admin
        self.output_queue: queue.Queue[str] = queue.Queue()
        self._proc = None
        self._pty = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if self._running:
            return

        if sys.platform == "win32" and _WINPTY_AVAILABLE:
            self._start_winpty()
        elif _PTY_AVAILABLE:
            self._start_pty()
        else:
            self._start_subprocess()

        self._running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def _start_winpty(self) -> None:
        """Start a pywinpty pseudo-console on Windows."""
        cmd = self._resolve_command()
        # pywinpty PTY.spawn expects a string command line
        if isinstance(cmd, list):
            cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        else:
            cmd_str = cmd
        self._pty = PTY(cols=120, rows=30)
        self._pty.spawn(cmd_str)
        logger.info("PTY (winpty) started: %s", cmd_str)

    def _start_pty(self) -> None:
        """Start a stdlib pty on POSIX."""
        import pty
        master, slave = openpty()
        self._proc = subprocess.Popen(
            self._resolve_command(),
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            shell=isinstance(self._resolve_command(), str),
        )
        self._pty = master
        os.close(slave)
        logger.info("PTY (stdlib) started: %s", self._resolve_command())

    def _start_subprocess(self) -> None:
        """Safe fallback: plain subprocess with pipes."""
        cmd = self._resolve_command()
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            bufsize=1,
        )
        logger.info("Subprocess fallback started: %s", cmd)

    # ------------------------------------------------------------------ #
    # I/O
    # ------------------------------------------------------------------ #
    def _resolve_command(self) -> list[str] | str:
        """Build the final command list, applying admin elevation if needed."""
        if isinstance(self.command, str):
            cmd = self.command
        elif isinstance(self.command, list):
            cmd = self.command
        else:
            cmd = str(self.command)

        if self.is_admin and sys.platform == "win32":
            if isinstance(cmd, list):
                cmd_str = " ".join(cmd)
            else:
                cmd_str = cmd
            return ["powershell.exe", "-Command",
                    f"Start-Process -FilePath 'cmd.exe' -ArgumentList '/k {cmd_str}' -Verb RunAs"]
        return cmd

    def write_input(self, data: str) -> None:
        """Send *data* (typically keyboard input) to the terminal."""
        try:
            if self._pty and _WINPTY_AVAILABLE:
                self._pty.write(data)
            elif self._pty:
                os.write(self._pty, data.encode("utf-8"))
            elif self._proc and self._proc.stdin and self._proc.stdin.writable():
                self._proc.stdin.write(data)
                self._proc.stdin.flush()
        except Exception as exc:
            logger.debug("write_input error: %s", exc)

    def read_available(self, timeout: float = 0.1) -> str:
        """Return buffered output, or wait briefly for new data."""
        chunks: list[str] = []

        if self._pty and _WINPTY_AVAILABLE:
            try:
                data = self._pty.read()
                while data:
                    chunks.append(data)
                    data = self._pty.read()
            except Exception:
                pass

        elif self._pty:
            import select
            try:
                ready, _, _ = select.select([self._pty], [], [], timeout)
                if ready:
                    data = os.read(self._pty, 4096)
                    chunks.append(data.decode("utf-8", errors="replace"))
            except Exception:
                pass

        elif self._proc and self._proc.stdout:
            try:
                data = self._proc.stdout.read(4096)
                if data:
                    chunks.append(data)
            except Exception:
                pass

        return "".join(chunks)

    # ------------------------------------------------------------------ #
    # Polling thread
    # ------------------------------------------------------------------ #
    def _poll(self) -> None:
        """Continuously read output and push into the queue."""
        import time
        while self._running:
            data = self.read_available(timeout=0.05)
            if data:
                self.output_queue.put(data)
            else:
                time.sleep(0.02)
            # Detect process exit
            if self._proc and self._proc.poll() is not None:
                self._running = False
                break
            if self._pty and _WINPTY_AVAILABLE:
                if not self._pty.isalive():
                    self._running = False
                    break

    # ------------------------------------------------------------------ #
    # Shutdown
    # ------------------------------------------------------------------ #
    def terminate(self) -> None:
        self._running = False
        try:
            if self._pty and _WINPTY_AVAILABLE:
                self._pty.close(force=True)
        except Exception:
            pass
        try:
            if self._proc:
                self._proc.terminate()
                self._proc.wait(timeout=3)
        except Exception:
            try:
                if self._proc:
                    self._proc.kill()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("PTY terminal terminated")

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def enable_vt_mode() -> None:
        """Enable Windows 10+ Virtual Terminal processing for native consoles."""
        if sys.platform != "win32":
            return
        kernel32 = ctypes.windll.kernel32
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        STD_OUTPUT_HANDLE = -11
        h = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if h != -1:
            kernel32.SetConsoleMode(h, ENABLE_VIRTUAL_TERMINAL_PROCESSING)
