"""Settings configuration screen for Command Center."""

from __future__ import annotations

from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Label, Static

from command_center.context_menu import (
    is_context_menu_registered,
    register_context_menu,
    unregister_context_menu,
)
from command_center.i18n import t
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
        lang = self.settings.language
        with Vertical(id="settings-dialog"):
            yield Label(t("settings_title", lang), id="settings-title")

            # Language selection
            yield Label(t("settings_lang_label", lang), id="lbl-lang", classes="settings-label")
            with Horizontal(classes="settings-row"):
                lang_name = "Français" if lang == "fr" else "English"
                yield Button(f"{t('settings_lang_btn', lang)}: {lang_name}", id="btn-lang-toggle", classes="settings-btn")

            # Theme selection
            yield Label(t("settings_theme_label", lang), id="lbl-theme", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(f"{t('settings_theme_btn', lang)}: {self.settings.theme}", id="btn-theme-cycle", classes="settings-btn")

            # Default shell
            yield Label(t("settings_shell_label", lang), id="lbl-shell", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"{t('settings_shell_btn', lang)}: {self.settings.default_shell.upper()}",
                    id="btn-shell-toggle",
                    classes="settings-btn",
                )

            # Library Enter Action
            yield Label(t("settings_lib_label", lang), id="lbl-lib-action", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"{t('settings_lib_btn', lang)}: {self.settings.library_enter_action.upper()}",
                    id="btn-lib-action-toggle",
                    classes="settings-btn",
                )

            # History output retention
            yield Label(t("settings_retention_label", lang), id="lbl-retention", classes="settings-label")
            with Horizontal(classes="settings-row"):
                yield Button(
                    f"{t('settings_retention_btn', lang)}: {self.settings.history_retention.upper()}",
                    id="btn-retention-toggle",
                    classes="settings-btn",
                )

            # Safety confirmation
            yield Label(t("settings_safety_label", lang), id="lbl-safety", classes="settings-label")
            with Horizontal(classes="settings-row"):
                status_str = t("safety_enabled_str", lang) if self.settings.safety_enabled else t("safety_disabled_str", lang)
                yield Button(
                    f"{t('settings_safety_btn', lang)}: {status_str}",
                    id="btn-safety-toggle",
                    classes="settings-btn",
                )

            # Explorer Context Menu
            yield Label(t("settings_context_menu_label", lang), id="lbl-context-menu", classes="settings-label")
            with Horizontal(classes="settings-row"):
                is_reg = is_context_menu_registered()
                cm_str = t("context_menu_enabled_str", lang) if is_reg else t("context_menu_disabled_str", lang)
                yield Button(
                    f"{t('settings_context_menu_btn', lang)}: {cm_str}",
                    id="btn-context-menu-toggle",
                    classes="settings-btn",
                )

            with Horizontal(id="settings-actions"):
                yield Button(t("settings_save_btn", lang), variant="primary", id="btn-settings-save")
                yield Button(t("settings_cancel_btn", lang), variant="default", id="btn-settings-cancel")

    def _refresh_labels(self) -> None:
        """Updates dialog texts to match active language and settings."""
        lang = self.settings.language
        try:
            self.query_one("#settings-title", Label).update(t("settings_title", lang))
            self.query_one("#lbl-lang", Label).update(t("settings_lang_label", lang))
            lang_name = "Français" if lang == "fr" else "English"
            self.query_one("#btn-lang-toggle", Button).label = f"{t('settings_lang_btn', lang)}: {lang_name}"
            self.query_one("#lbl-theme", Label).update(t("settings_theme_label", lang))
            self.query_one("#btn-theme-cycle", Button).label = f"{t('settings_theme_btn', lang)}: {self.settings.theme}"
            self.query_one("#lbl-shell", Label).update(t("settings_shell_label", lang))
            self.query_one("#btn-shell-toggle", Button).label = f"{t('settings_shell_btn', lang)}: {self.settings.default_shell.upper()}"
            self.query_one("#lbl-lib-action", Label).update(t("settings_lib_label", lang))
            self.query_one("#btn-lib-action-toggle", Button).label = f"{t('settings_lib_btn', lang)}: {self.settings.library_enter_action.upper()}"
            self.query_one("#lbl-retention", Label).update(t("settings_retention_label", lang))
            self.query_one("#btn-retention-toggle", Button).label = f"{t('settings_retention_btn', lang)}: {self.settings.history_retention.upper()}"
            self.query_one("#lbl-safety", Label).update(t("settings_safety_label", lang))
            status_str = t("safety_enabled_str", lang) if self.settings.safety_enabled else t("safety_disabled_str", lang)
            self.query_one("#btn-safety-toggle", Button).label = f"{t('settings_safety_btn', lang)}: {status_str}"
            self.query_one("#lbl-context-menu", Label).update(t("settings_context_menu_label", lang))
            is_reg = is_context_menu_registered()
            cm_str = t("context_menu_enabled_str", lang) if is_reg else t("context_menu_disabled_str", lang)
            self.query_one("#btn-context-menu-toggle", Button).label = f"{t('settings_context_menu_btn', lang)}: {cm_str}"
            self.query_one("#btn-settings-save", Button).label = t("settings_save_btn", lang)
            self.query_one("#btn-settings-cancel", Button).label = t("settings_cancel_btn", lang)
        except Exception:
            pass

    @on(Button.Pressed, "#btn-lang-toggle")
    def toggle_language(self) -> None:
        self.settings.language = "fr" if self.settings.language == "en" else "en"
        self._refresh_labels()

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

    @on(Button.Pressed, "#btn-context-menu-toggle")
    def toggle_context_menu(self) -> None:
        if is_context_menu_registered():
            unregister_context_menu()
        else:
            register_context_menu()
        lang = self.settings.language
        is_reg = is_context_menu_registered()
        cm_str = t("context_menu_enabled_str", lang) if is_reg else t("context_menu_disabled_str", lang)
        self.query_one("#btn-context-menu-toggle", Button).label = f"{t('settings_context_menu_btn', lang)}: {cm_str}"

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
