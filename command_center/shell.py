"""Persistent shell sessions for Command Center."""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from typing import Callable, Optional, Tuple

INTERACTIVE_COMMANDS = {
    "vim",
    "vi",
    "nano",
    "top",
    "htop",
    "less",
    "more",
    "ssh",
}


class ShellSession:
    """Manages a long-running shell process (PowerShell / cmd)."""

    def __init__(self, shell_type: str = "powershell") -> None:
        self.shell_type = shell_type.lower()
        self.process: Optional[subprocess.Popen] = None
        self.cwd: str = os.getcwd()
        self.is_running_command: bool = False
        self.start()

    def start(self) -> None:
        """Starts or restarts the persistent shell process."""
        self.close()
        if self.shell_type == "powershell":
            cmd = [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NoExit",
                "-Command",
                "-",
            ]
        elif self.shell_type == "cmd":
            cmd = ["cmd.exe", "/Q", "/K"]
        else:
            raise ValueError(f"Unsupported shell: {self.shell_type}")

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=self.cwd,
            encoding="utf-8",
            errors="replace",
        )
        self.is_running_command = False

    def close(self) -> None:
        """Terminates the underlying shell process if running."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        self.is_running_command = False

    def restart(self) -> None:
        """Restarts the session in the current working directory."""
        self.start()

    def interrupt(self) -> None:
        """Interrupts a running command by restarting the session."""
        # On Windows stdin pipes, restarting the session is the reliable interrupt
        self.restart()

    def execute(
        self,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> Tuple[int, str, int]:
        """
        Executes a command within the persistent shell session.

        Args:
            command: The command string to execute.
            on_output: Optional callback invoked with each output line as it arrives.

        Returns:
            Tuple of (exit_code, new_cwd, duration_ms).
        """
        stripped_cmd = command.strip()
        if not stripped_cmd:
            return 0, self.cwd, 0

        # Disallow full-screen interactive tools for v1
        lead_word = stripped_cmd.split()[0].lower()
        if lead_word in INTERACTIVE_COMMANDS:
            msg = (
                f"[Command Center] '{lead_word}' is an interactive full-screen program, "
                "which is not supported in v1.\n"
            )
            if on_output:
                on_output(msg)
            return 1, self.cwd, 0

        if not self.process or self.process.poll() is not None:
            self.start()

        token = f"__CC_DONE_{uuid.uuid4().hex}__"
        start_time = time.perf_counter()
        self.is_running_command = True

        if self.shell_type == "powershell":
            payload = (
                "$LASTEXITCODE = $null\n"
                f"{stripped_cmd}\n"
                "$cc_ec = if ($LASTEXITCODE -ne $null) { $LASTEXITCODE } else { if ($?) { 0 } else { 1 } }\n"
                f'Write-Output "{token} $cc_ec $($PWD.Path)"\n'
            )
        else:
            # cmd support (will be fully tested in step 3)
            payload = (
                f"{stripped_cmd}\n"
                f"@echo {token} %ERRORLEVEL% %CD%\n"
            )

        try:
            assert self.process and self.process.stdin
            self.process.stdin.write(payload)
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            self.start()
            return 1, self.cwd, int((time.perf_counter() - start_time) * 1000)

        exit_code = 0
        new_cwd = self.cwd

        assert self.process and self.process.stdout
        while True:
            line = self.process.stdout.readline()
            if not line:
                # Process ended unexpectedly
                break

            if token in line:
                # Sentinel detected: extract exit code and cwd
                clean_line = line.strip()
                # Find start of sentinel token
                idx = clean_line.find(token)
                sentinel_part = clean_line[idx:]
                parts = sentinel_part.split(" ", 2)
                try:
                    if len(parts) > 1:
                        exit_code = int(parts[1])
                except ValueError:
                    exit_code = 0
                if len(parts) > 2 and parts[2].strip():
                    new_cwd = parts[2].strip()
                    self.cwd = new_cwd
                break

            if on_output:
                on_output(line)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        self.is_running_command = False
        return exit_code, new_cwd, duration_ms
