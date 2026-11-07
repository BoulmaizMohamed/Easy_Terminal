"""Settings configuration screen for Command Center."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Static

from command_center.settings import AppSettings, save_settings

AVAILABLE_THEMES = [
    "catppuccin-mocha",
    "nord",
    "tokyo-night",
    "dracula",
    "textual-dark",
    "catppuccin-latte",
    "textual-light",
]


class SettingsScreen(ModalScreen[Optional[AppSettings]]):
    """Configuration modal to customize Command Center preferences."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True, priority=True),
        Binding("enter", "save", "Save", show=True, priority=True),
    ]

    def __init__(self, current_settings: AppSettings, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = AppSettings(**vars(current_settings))
        self.theme_idx = AVAILABLE_THEMES.index(self.settings.theme) if self.settings.theme in AVAILABLE_THEMES else 0

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-dialog"):
            yield Label("SETTINGS & PREFERENCES", id="settings-title")

            # Theme selection
            yield Label("Interface Theme:", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(f"Theme: {self.settings.theme}", id="btn-theme-cycle", classes="settings-btn")

            # Default shell
            yield Label("Default Shell:", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"Shell: {self.settings.default_shell.upper()}",
                    id="btn-shell-toggle",
                    classes="settings-btn",
                )

            # Library Enter Action
            yield Label("Library Enter Behavior:", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"Enter Action: {self.settings.library_enter_action.upper()}",
                    id="btn-lib-action-toggle",
                    classes="settings-btn",
                )

            # History output retention
            yield Label("History Output Retention:", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"Retention: {self.settings.history_retention.upper()}",
                    id="btn-retention-toggle",
                    classes="settings-btn",
                )

            # Safety confirmation
            yield Label("Dangerous Command Safety Check:", classes="settings-label")
            with Horizontal(classes="settings-row"):
                status_str = "ENABLED (Confirm before run)" if self.settings.safety_enabled else "DISABLED"
                yield Button(
                    f"Safety: {status_str}",
                    id="btn-safety-toggle",
                    classes="settings-btn",
                )

            with Horizontal(id="settings-actions"):
                yield Button("Save Preferences (Enter)", variant="primary", id="btn-settings-save")
                yield Button("Cancel (Esc)", variant="default", id="btn-settings-cancel")

    @on(Button.Pressed, "#btn-theme-cycle")
    def cycle_theme(self) -> None:
        self.theme_idx = (self.theme_idx + 1) % len(AVAILABLE_THEMES)
        self.settings.theme = AVAILABLE_THEMES[self.theme_idx]
        self.app.theme = self.settings.theme
        self.query_one("#btn-theme-cycle", Button).label = f"Theme: {self.settings.theme}"

    @on(Button.Pressed, "#btn-shell-toggle")
    def toggle_default_shell(self) -> None:
        new_shell = "cmd" if self.settings.default_shell == "powershell" else "powershell"
        self.settings.default_shell = new_shell
        self.query_one("#btn-shell-toggle", Button).label = f"Shell: {new_shell.upper()}"

    @on(Button.Pressed, "#btn-lib-action-toggle")
    def toggle_lib_action(self) -> None:
        new_act = "insert" if self.settings.library_enter_action == "run" else "run"
        self.settings.library_enter_action = new_act
        self.query_one("#btn-lib-action-toggle", Button).label = f"Enter Action: {new_act.upper()}"

    @on(Button.Pressed, "#btn-retention-toggle")
    def toggle_retention(self) -> None:
        new_ret = "off" if self.settings.history_retention == "preview" else "preview"
        self.settings.history_retention = new_ret
        self.query_one("#btn-retention-toggle", Button).label = f"Retention: {new_ret.upper()}"

    @on(Button.Pressed, "#btn-safety-toggle")
    def toggle_safety(self) -> None:
        self.settings.safety_enabled = not self.settings.safety_enabled
        status_str = "ENABLED (Confirm before run)" if self.settings.safety_enabled else "DISABLED"
        self.query_one("#btn-safety-toggle", Button).label = f"Safety: {status_str}"

    @on(Button.Pressed, "#btn-settings-save")
    def on_save_pressed(self) -> None:
        self.action_save()

    @on(Button.Pressed, "#btn-settings-cancel")
    def on_cancel_pressed(self) -> None:
        self.action_cancel()

    def action_save(self) -> None:
        save_settings(self.settings)
        self.dismiss(self.settings)

    def action_cancel(self) -> None:
        self.dismiss(None)
