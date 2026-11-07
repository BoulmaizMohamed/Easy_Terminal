"""Safety confirmation modal dialog for dangerous commands."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class SafetyConfirmationDialog(ModalScreen[bool]):
    """Warning modal shown before executing destructive commands."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "confirm", "Run Anyway", show=True),
    ]

    def __init__(self, command: str, reason: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.command = command
        self.reason = reason

    def compose(self) -> ComposeResult:
        with Vertical(id="safety-dialog"):
            yield Label("POTENTIALLY DESTRUCTIVE COMMAND", id="safety-title")
            yield Label(f"Reason: {self.reason}", id="safety-reason")

            with Container(id="safety-command-box"):
                yield Label(self.command, id="safety-command-text")

            yield Label("The shell is yours. Are you sure you want to run this command?", id="safety-prompt")

            with Horizontal(id="safety-actions"):
                yield Button("Run Anyway (Enter)", variant="error", id="btn-safety-confirm")
                yield Button("Cancel (Esc)", variant="default", id="btn-safety-cancel")

    def on_mount(self) -> None:
        # Default focus to Cancel for defensive safety
        self.query_one("#btn-safety-cancel", Button).focus()

    @on(Button.Pressed, "#btn-safety-confirm")
    def on_confirm_pressed(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#btn-safety-cancel")
    def on_cancel_pressed(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
