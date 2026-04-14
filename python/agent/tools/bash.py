import os
import queue
import shutil
import subprocess
import threading
import time
import uuid


def tool_info():
    return {
        "name": "bash",
        "description": "Run shell commands. Input MUST be a JSON object with a single 'command' key. Example: {\"command\": \"ls -R\"}",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run."
                }
            },
            "required": ["command"]
        }
    }


class ShellSession:
    """A persistent shell session with cross-platform shell selection."""

    def __init__(self):
        self._started = False
        self._process = None
        self._reader_thread = None
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._timeout = 120.0
        self._shell_kind = None

    def _detect_shell(self):
        if os.name == "nt":
            for shell_name in ("pwsh", "powershell"):
                shell_path = shutil.which(shell_name)
                if shell_path:
                    return [shell_path, "-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"], "powershell"
            return [os.environ.get("COMSPEC", "cmd.exe"), "/Q", "/K"], "cmd"

        shell_path = (
            shutil.which("bash")
            or os.environ.get("SHELL")
            or shutil.which("sh")
            or "/bin/sh"
        )
        return [shell_path], "posix"

    def _reader_loop(self):
        if self._process is None or self._process.stdout is None:
            return

        for line in iter(self._process.stdout.readline, ""):
            self._queue.put(line)

    def _drain_queue(self):
        drained = []
        while True:
            try:
                drained.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return drained

    def _write_line(self, line):
        if self._process is None or self._process.stdin is None:
            raise ValueError("Shell session is not started.")
        self._process.stdin.write(line + "\n")
        self._process.stdin.flush()

    def _initialize_shell(self):
        if self._shell_kind == "powershell":
            self._write_line("function prompt { '' }")
            self._write_line("$ProgressPreference = 'SilentlyContinue'")
        elif self._shell_kind == "cmd":
            self._write_line("prompt")
        else:
            self._write_line("export PS1=''")

        sentinel = f"<<shell-ready:{uuid.uuid4().hex}>>"
        self._write_line(self._sentinel_command(sentinel))
        self._wait_for_sentinel(sentinel)

    def start(self):
        if self._started:
            return

        shell_cmd, self._shell_kind = self._detect_shell()
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        self._process = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=os.environ.copy(),
            creationflags=creationflags,
        )
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()
        self._started = True
        time.sleep(0.1)
        self._drain_queue()
        self._initialize_shell()

    def stop(self):
        if not self._started:
            return
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
        self._process = None
        self._started = False

    def _sentinel_command(self, sentinel):
        if self._shell_kind == "powershell":
            return f"Write-Output '{sentinel}'"
        if self._shell_kind == "cmd":
            return f"echo {sentinel}"
        return f"printf '{sentinel}\\n'"

    def _wait_for_sentinel(self, sentinel):
        lines = []
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self._timeout:
                self.stop()
                raise ValueError(
                    f"Timed out: shell has not returned in {self._timeout} seconds and must be restarted."
                )

            try:
                line = self._queue.get(timeout=min(0.5, self._timeout - elapsed))
            except queue.Empty:
                continue

            if sentinel in line:
                before_sentinel = line.split(sentinel, 1)[0]
                if before_sentinel.strip():
                    lines.append(before_sentinel)
                break
            lines.append(line)

        return "".join(lines).strip()

    def run(self, command):
        with self._lock:
            if not self._started:
                self.start()

            if self._process is None or self._process.poll() is not None:
                raise ValueError("Shell has exited and must be restarted.")

            self._drain_queue()
            sentinel = f"<<exit:{uuid.uuid4().hex}>>"
            self._write_line(command)
            self._write_line(self._sentinel_command(sentinel))
            output = self._wait_for_sentinel(sentinel)
            return output, ""


def filter_output(output):
    filtered_lines = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            filtered_lines.append(line)
            continue
        if "Inappropriate ioctl for device" in stripped:
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines).strip()


_shell_session = ShellSession()


def tool_function(command):
    try:
        output, error = _shell_session.run(command)
        result = filter_output(output)
        if error:
            if result:
                result += "\nError:\n" + error
            else:
                result = "Error:\n" + error
        return result.strip()
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bash.py '<command>'")
    else:
        input_command = " ".join(sys.argv[1:])
        print(tool_function(input_command))
