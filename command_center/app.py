"""Command Center - Main Textual Application."""

from __future__ import annotations

import os
from typing import List

import pyperclip
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Input, Label, RichLog, Static

from command_center.db import init_db
from command_center.history import get_recent_unique_commands, log_command
from command_center.history_screen import HistoryScreen
from command_center.shell import ShellManager, ShellSession

THEMES = [
    "catppuccin-mocha",
    "nord",
    "tokyo-night",
    "dracula",
    "textual-dark",
    "catppuccin-latte",
    "textual-light",
]


class CommandCenterApp(App):
    """Command Center Desktop Terminal Front-End."""

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f2", "toggle_shell", "Switch Shell (F2)", show=True),
        Binding("ctrl+t", "toggle_theme", "Theme", show=True),
        Binding("ctrl+h", "open_history", "History", show=True),
        Binding("ctrl+c", "interrupt_or_clear", "Interrupt/Clear", show=True),
        Binding("ctrl+r", "restart_shell", "Restart Shell", show=True),
        Binding("ctrl+y", "copy_last_output", "Copy Output", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.shell_manager = ShellManager("powershell")
        self.theme_index = 0
        self.theme = THEMES[0]
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.last_output_buffer: List[str] = []
        self.current_running_command: str = ""

    @property
    def shell(self) -> ShellSession:
        """Returns the active persistent shell session."""
        return self.shell_manager.current

    def compose(self) -> ComposeResult:
        """Compose the layout of the terminal UI."""
        with Horizontal(id="header-bar"):
            yield Label("COMMAND CENTER", id="app-title")
            yield Label("v0.1.0 - Modern Terminal Front-End", id="app-subtitle")

        with Container(id="output-container"):
            yield RichLog(
                id="output-log",
                highlight=True,
                markup=True,
                wrap=True,
            )

        with Horizontal(id="input-container"):
            yield Static(">", id="prompt-symbol")
            yield Input(
                id="command-input",
                placeholder="Type a PowerShell command and press Enter...",
            )

        with Horizontal(id="status-bar"):
            yield Static(
                f"{self.shell.shell_type.upper()}",
                id="status-shell",
                classes="status-badge",
            )
            yield Static(
                f"{self.shell.cwd}",
                id="status-cwd",
                classes="status-badge",
            )
            yield Static(
                "Exit: 0",
                id="status-exit",
                classes="status-badge",
            )
            yield Static(
                "Ready",
                id="status-state",
                classes="status-badge",
            )

        yield Footer()

    def on_mount(self) -> None:
        """Run on application startup."""
        try:
            init_db()
            saved_recent = get_recent_unique_commands(shell=self.shell.shell_type)
            if saved_recent:
                self.command_history.extend(saved_recent)
        except Exception:
            pass

        log = self.query_one(RichLog)
        log.write("[bold cyan]Welcome to Command Center[/bold cyan]")
        log.write(
            f"[dim]Running real persistent [bold]{self.shell.shell_type}[/bold] session. "
            f"Directory: {self.shell.cwd}[/dim]\n"
        )
        self.query_one(Input).focus()

    @on(Input.Submitted, "#command-input")
    def handle_command_submit(self, event: Input.Submitted) -> None:
        """Called when a command is submitted from the input line."""
        cmd = event.value.strip()
        if not cmd:
            return

        input_widget = self.query_one(Input)
        input_widget.value = ""
        self.current_running_command = cmd

        # Track in history
        if not self.command_history or self.command_history[-1] != cmd:
            self.command_history.append(cmd)
        self.history_index = -1

        # Render command banner in output
        log = self.query_one(RichLog)
        log.write(f"\n[bold magenta]>[/bold magenta] [bold white]{cmd}[/bold white]")

        # Update status
        self._set_state_running()

        # Execute off the UI thread
        self.run_command_in_background(cmd)

    @work(thread=True)
    def run_command_in_background(self, cmd: str) -> None:
        """Runs the command in the persistent shell worker thread."""
        current_buffer: List[str] = []

        def on_chunk(chunk: str) -> None:
            current_buffer.append(chunk)
            self.call_from_thread(self._append_chunk, chunk)

        exit_code, new_cwd, duration_ms = self.shell.execute(cmd, on_output=on_chunk)
        self.last_output_buffer = current_buffer
        self.call_from_thread(self._on_command_finished, exit_code, new_cwd, duration_ms)

    def _append_chunk(self, chunk: str) -> None:
        """Appends output chunks safely onto the RichLog widget."""
        log = self.query_one(RichLog)
        # Strip trailing newline because RichLog.write appends one
        clean_text = chunk.rstrip("\r\n")
        if clean_text:
            log.write(clean_text)

    def _on_command_finished(self, exit_code: int, new_cwd: str, duration_ms: int) -> None:
        """Updates the status and UI once command execution completes."""
        log = self.query_one(RichLog)
        ec_color = "green" if exit_code == 0 else "red"
        log.write(
            f"[dim]-- exit: [{ec_color}]{exit_code}[/{ec_color}] | {duration_ms}ms[/dim]"
        )

        # Log into SQLite history
        if self.current_running_command:
            preview = "".join(self.last_output_buffer)
            try:
                log_command(
                    command=self.current_running_command,
                    shell=self.shell.shell_type,
                    cwd=new_cwd,
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    output_preview=preview,
                )
            except Exception:
                pass
            self.current_running_command = ""

        # Update status bar
        status_state = self.query_one("#status-state", Static)
        status_state.update("Ready")

        status_cwd = self.query_one("#status-cwd", Static)
        status_cwd.update(f"{new_cwd}")

        # Update exit code badge
        exit_badge = self.query_one("#status-exit", Static)
        if exit_code == 0:
            exit_badge.update("Exit: [green]0[/green]")
        else:
            exit_badge.update(f"Exit: [red]{exit_code}[/red]")

        self.query_one(Input).focus()

    def _set_state_running(self) -> None:
        """Set status bar to running state."""
        status_state = self.query_one("#status-state", Static)
        status_state.update("Running...")

    @on(Input.Changed, "#command-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Hook for future auto-suggest integration."""
        pass

    def action_open_history(self) -> None:
        """Opens the History screen."""
        self.push_screen(HistoryScreen(), self._on_history_screen_result)

    def _on_history_screen_result(self, cmd: Optional[str]) -> None:
        """Callback when a command is selected from the History screen."""
        if cmd:
            input_widget = self.query_one(Input)
            input_widget.value = cmd
            input_widget.focus()
            self.handle_command_submit(Input.Submitted(input_widget, cmd))

    def action_toggle_shell(self) -> None:
        """Toggles active shell between PowerShell and CMD with F2."""
        new_shell = self.shell_manager.toggle()
        shell_name = "PowerShell" if new_shell == "powershell" else "Command Prompt (CMD)"
        log = self.query_one(RichLog)
        log.write(f"\n[dim]-- Switched active shell to [bold cyan]{shell_name}[/bold cyan] --[/dim]")

        # Update status bar
        status_shell = self.query_one("#status-shell", Static)
        status_shell.update(f"{new_shell.upper()}")

        status_cwd = self.query_one("#status-cwd", Static)
        status_cwd.update(f"{self.shell.cwd}")

        # Update input placeholder
        inp = self.query_one("#command-input", Input)
        inp.placeholder = f"Type a {shell_name} command and press Enter..."

        self.notify(f"Active shell: {shell_name}", timeout=2)

    def on_unmount(self) -> None:
        """Cleanly terminate shell processes upon app exit."""
        self.shell_manager.close_all()

    def action_toggle_theme(self) -> None:
        """Cycles through clean modern themes."""
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        new_theme = THEMES[self.theme_index]
        self.theme = new_theme
        self.notify(f"Theme switched to: {new_theme}", timeout=2)

    def action_interrupt_or_clear(self) -> None:
        """Interrupts running command or clears current input text."""
        input_widget = self.query_one(Input)
        if self.shell.is_running_command:
            self.shell.interrupt()
            log = self.query_one(RichLog)
            log.write("[bold yellow]^C (Interrupted / Session Reset)[/bold yellow]")
            self._on_command_finished(130, self.shell.cwd, 0)
        elif input_widget.value:
            input_widget.value = ""

    def action_restart_shell(self) -> None:
        """Explicitly restarts the persistent shell session."""
        self.shell.restart()
        log = self.query_one(RichLog)
        log.write("[bold yellow]Shell session restarted.[/bold yellow]")
        self.query_one("#status-cwd", Static).update(f"{self.shell.cwd}")
        self.notify("Persistent shell session restarted.", timeout=2)

    def action_copy_last_output(self) -> None:
        """Copies the output of the most recent command to the clipboard."""
        if not self.last_output_buffer:
            self.notify("No command output to copy.", severity="warning")
            return
        text = "".join(self.last_output_buffer)
        try:
            pyperclip.copy(text)
            self.notify("Copied last command output to clipboard!", timeout=2)
        except Exception as e:
            self.notify(f"Clipboard error: {e}", severity="error")

    def key_up(self) -> None:
        """Cycle up through command history."""
        input_widget = self.query_one(Input)
        if not input_widget.has_focus or not self.command_history:
            return

        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1

        input_widget.value = self.command_history[self.history_index]
        input_widget.cursor_position = len(input_widget.value)

    def key_down(self) -> None:
        """Cycle down through command history."""
        input_widget = self.query_one(Input)
        if not input_widget.has_focus or not self.command_history:
            return

        if self.history_index != -1:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                input_widget.value = self.command_history[self.history_index]
            else:
                self.history_index = -1
                input_widget.value = ""
            input_widget.cursor_position = len(input_widget.value)


def main() -> None:
    """Entry point for running Command Center."""
    app = CommandCenterApp()
    app.run()


if __name__ == "__main__":
    main()
