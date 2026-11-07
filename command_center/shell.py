"""Persistent shell sessions for Command Center."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time
import uuid
from typing import Callable, Dict, Optional, Tuple

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

    def __init__(self, shell_type: str = "powershell", cwd: Optional[str] = None) -> None:
        self.shell_type = shell_type.lower()
        self.process: Optional[subprocess.Popen] = None
        self.cwd: str = str(Path(cwd).resolve()) if cwd and Path(cwd).exists() else os.getcwd()
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

        # For cmd.exe, silence prompts to keep output pristine
        if self.shell_type == "cmd":
            init_token = f"__CC_INIT_{uuid.uuid4().hex}__"
            assert self.process and self.process.stdin and self.process.stdout
            self.process.stdin.write(f"@echo off\n@prompt $_\n@echo {init_token}\n")
            self.process.stdin.flush()
            while True:
                line = self.process.stdout.readline()
                if init_token in line or not line:
                    break

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
        self.restart()

    def sync_cwd(self, target_cwd: str) -> None:
        """Synchronizes the shell session's working directory to target_cwd."""
        if not target_cwd or target_cwd == self.cwd:
            return
        if self.shell_type == "powershell":
            escaped = target_cwd.replace("'", "''")
            self.execute(f"Set-Location -LiteralPath '{escaped}'")
        else:
            self.execute(f'cd /d "{target_cwd}"')

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
                f"[Easy_Terminal] '{lead_word}' is an interactive full-screen program, "
                "which is not supported in the embedded stream console.\n"
                "Tip: To edit files, use 'notepad <filename>'; to view contents, use 'type <filename>'.\n"
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
            payload = (
                f"{stripped_cmd}\n"
                f"@echo off & @echo {token} %ERRORLEVEL% %CD%\n"
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
                break

            if token in line:
                clean_line = line.strip()
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


class ShellManager:
    """Coordinates persistent cmd and PowerShell sessions with smooth switching."""

    def __init__(self, default_shell: str = "powershell", cwd: Optional[str] = None) -> None:
        self.sessions: Dict[str, ShellSession] = {
            "powershell": ShellSession("powershell", cwd=cwd),
            "cmd": ShellSession("cmd", cwd=cwd),
        }
        self.active_shell: str = default_shell.lower()

    @property
    def current(self) -> ShellSession:
        return self.sessions[self.active_shell]

    def toggle(self) -> str:
        """Toggles between PowerShell and CMD, syncing working directories."""
        old_shell = self.active_shell
        new_shell = "cmd" if old_shell == "powershell" else "powershell"
        current_cwd = self.sessions[old_shell].cwd
        self.sessions[new_shell].sync_cwd(current_cwd)
        self.active_shell = new_shell
        return new_shell

    def close_all(self) -> None:
        """Terminates all managed shell processes."""
        for session in self.sessions.values():
            session.close()
