import subprocess
import threading
import queue
import ctypes, sys

class TerminalProcessEngine:
    def __init__(self, command: str, is_admin: bool = False):
        self.command = command
        self.is_admin = is_admin
        self.process = None
        self.output_queue = queue.Queue()
        self.is_running = False

    def start(self):
        cmd = self.command
        # Nếu yêu cầu Run as Admin trên Windows
        if self.is_admin and sys.platform == 'win32':
            # Thực thi bằng PowerShell Start-Process Verb RunAs
            cmd = f'powershell -Command "Start-Process {self.command} -Verb RunAs"'

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            bufsize=1
        )
        self.is_running = True
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self):
        while self.is_running and self.process.poll() is None:
            char = self.process.stdout.read(1)
            if char:
                self.output_queue.put(char)
            else:
                break
        self.is_running = False

    def write_input(self, data: str):
        if self.process and self.process.stdin and self.is_running:
            self.process.stdin.write(data)
            self.process.stdin.flush()

    def terminate(self):
        self.is_running = False
        if self.process:
            self.process.terminate()