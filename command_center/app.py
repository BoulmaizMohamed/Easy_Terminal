"""Command Center - Main Textual Application."""

from __future__ import annotations

import os
from typing import List, Optional

import pyperclip
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text
from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Input, Label, OptionList, RichLog, Static
from textual.widgets.option_list import Option

from command_center.db import init_db
from command_center.git_info import get_location_info
from command_center.history import get_recent_unique_commands, log_command
from command_center.history_screen import HistoryScreen
from command_center.i18n import t
from command_center.library import load_seed_library
from command_center.library_screen import LibraryScreen
from command_center.palette_screen import PaletteScreen
from command_center.safety import is_dangerous_command
from command_center.safety_dialog import SafetyConfirmationDialog
from command_center.settings import AppSettings, load_settings, save_settings
from command_center.settings_screen import SettingsScreen
from command_center.shell import ShellManager, ShellSession
from command_center.suggest import Suggestion, rank_suggestions

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
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("f2", "toggle_shell", "Switch Shell (F2)", show=True),
        Binding("ctrl+t", "toggle_theme", "Theme", show=True),
        Binding("ctrl+p", "open_palette", "Palette/Help", show=True),
        Binding("ctrl+l", "open_library", "Library", show=True),
        Binding("ctrl+h", "open_history", "History", show=True),
        Binding("f10", "open_settings", "Settings (F10)", show=True),
        Binding("ctrl+c", "interrupt_or_clear", "Interrupt/Clear", show=True),
        Binding("ctrl+r", "restart_shell", "Restart Shell", show=True),
        Binding("ctrl+y", "copy_last_output", "Copy Output", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = load_settings()
        self.shell_manager = ShellManager(self.settings.default_shell)
        self.theme = self.settings.theme
        self.theme_index = THEMES.index(self.theme) if self.theme in THEMES else 0
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.last_output_buffer: List[str] = []
        self.current_running_command: str = ""
        self.current_suggestions: List[Suggestion] = []
        self._active_run_id: int = 0

    @property
    def shell(self) -> ShellSession:
        """Returns the active persistent shell session."""
        return self.shell_manager.current

    def _render_prompt_symbol(self) -> str:
        """Renders styled prompt with shell type, directory/repo indicator and arrow."""
        loc = get_location_info(self.shell.cwd)
        shell_glyph = "PS" if self.shell.shell_type == "powershell" else "CMD"
        prompt_color = "cyan" if self.shell.shell_type == "powershell" else "yellow"
        badge = loc.get_prompt_badge()
        return f"[{prompt_color} bold]{shell_glyph}[/{prompt_color} bold] [dim {prompt_color}]{badge}[/dim {prompt_color}] [{prompt_color} bold]❯[/{prompt_color} bold]"

    def compose(self) -> ComposeResult:
        """Compose the layout of the terminal UI."""
        lang = self.settings.language
        prompt_color = "cyan" if self.shell.shell_type == "powershell" else "yellow"

        with Horizontal(id="header-bar"):
            yield Label("⚡ COMMAND CENTER", id="app-title")
            yield Label(t("app_subtitle", lang), id="app-subtitle")
            yield Static("", id="header-spacer")
            yield Label(f"[bold {prompt_color}]{self.shell.shell_type.upper()}[/bold {prompt_color}]  •  [dim]{t('header_settings', lang)}[/dim]", id="header-hints")

        with Container(id="output-container"):
            yield RichLog(
                id="output-log",
                highlight=True,
                markup=True,
                wrap=True,
                max_lines=5000,
            )

        with Vertical(id="bottom-dock"):
            with Horizontal(id="quick-actions-bar"):
                yield Button(t("qa_files", lang), id="qa-files", classes="qa-btn")
                yield Button(t("qa_procs", lang), id="qa-procs", classes="qa-btn")
                yield Button(t("qa_disks", lang), id="qa-disks", classes="qa-btn")
                yield Button(t("qa_ping", lang), id="qa-ping", classes="qa-btn")
                yield Button(t("qa_library", lang), id="qa-library", classes="qa-btn")
                yield Button(t("qa_shell", lang), id="qa-shell", classes="qa-btn")
                yield Button(t("qa_clear", lang), id="qa-clear", classes="qa-btn")

            with Horizontal(id="input-container"):
                yield Static(self._render_prompt_symbol(), id="prompt-symbol")
                ph = t("placeholder_ps", lang) if self.shell.shell_type == "powershell" else t("placeholder_cmd", lang)
                yield Input(
                    id="command-input",
                    placeholder=ph,
                )

            with Container(id="suggestions-container"):
                yield OptionList(id="suggestions-list")

            with Horizontal(id="status-bar"):
                loc = get_location_info(self.shell.cwd)
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
                    loc.get_repo_badge(lang),
                    id="status-repo",
                    classes="status-badge",
                )
                yield Static(
                    f"{t('status_exit', lang)}: 0",
                    id="status-exit",
                    classes="status-badge",
                )
                yield Static(
                    t("status_ready", lang),
                    id="status-state",
                    classes="status-badge",
                )

        yield Footer()

    def _refresh_ui_language(self) -> None:
        """Updates all visible UI labels and badges according to active language."""
        lang = self.settings.language
        prompt_color = "cyan" if self.shell.shell_type == "powershell" else "yellow"
        try:
            self.query_one("#app-subtitle", Label).update(t("app_subtitle", lang))
            self.query_one("#header-hints", Label).update(
                f"[bold {prompt_color}]{self.shell.shell_type.upper()}[/bold {prompt_color}]  •  [dim]{t('header_settings', lang)}[/dim]"
            )
            self.query_one("#qa-files", Button).label = t("qa_files", lang)
            self.query_one("#qa-procs", Button).label = t("qa_procs", lang)
            self.query_one("#qa-disks", Button).label = t("qa_disks", lang)
            self.query_one("#qa-ping", Button).label = t("qa_ping", lang)
            self.query_one("#qa-library", Button).label = t("qa_library", lang)
            self.query_one("#qa-shell", Button).label = t("qa_shell", lang)
            self.query_one("#qa-clear", Button).label = t("qa_clear", lang)

            ph = t("placeholder_ps", lang) if self.shell.shell_type == "powershell" else t("placeholder_cmd", lang)
            self.query_one("#command-input", Input).placeholder = ph

            loc = get_location_info(self.shell.cwd)
            self.query_one("#status-repo", Static).update(loc.get_repo_badge(lang))
            self.query_one("#status-state", Static).update(t("status_ready", lang))
            self.query_one("#prompt-symbol", Static).update(self._render_prompt_symbol())
        except Exception:
            pass

    def on_mount(self) -> None:
        """Run on application startup."""
        try:
            init_db()
            load_seed_library()
            saved_recent = get_recent_unique_commands(shell=self.shell.shell_type)
            if saved_recent:
                self.command_history.extend(saved_recent)
        except Exception:
            pass

        loc = get_location_info(self.shell.cwd)
        lang = self.settings.language
        log = self.query_one(RichLog)
        shell_badge_color = "cyan" if self.shell.shell_type == "powershell" else "yellow"
        welcome_body = Text()

        if lang == "fr":
            welcome_body.append("⚡ COMMAND CENTER ", style="bold cyan")
            welcome_body.append("— Espace de travail terminal moderne pour Windows\n\n", style="bold white")
            welcome_body.append("Shell actif : ", style="bold")
            welcome_body.append(f"{self.shell.shell_type.upper()} ", style=f"bold {shell_badge_color}")
            welcome_body.append("• Emplacement : ", style="dim")
            welcome_body.append(f"{self.shell.cwd}\n", style="dim cyan")
            if loc.is_git:
                welcome_body.append("• Dépôt Git : ", style="dim")
                welcome_body.append(f"{loc.repo_name} [{loc.branch}]\n\n", style="bold green")
            else:
                welcome_body.append(f"• Racine disque : {loc.root}\n\n", style="dim")
            welcome_body.append("Démarrage rapide pour débutants :\n", style="bold white")
            welcome_body.append("  • Cliquez sur un bouton d'action rapide ci-dessous (Fichiers, Applications, Disques, Ping)\n", style="cyan")
            welcome_body.append("  • Appuyez sur [Ctrl+L] pour parcourir 86 commandes quotidiennes et spécialisées\n", style="cyan")
            welcome_body.append("  • Appuyez sur [Ctrl+P] pour la palette de commandes et recherche rapide\n", style="cyan")
            welcome_body.append("  • Tapez 'clear' ou 'cls' à tout moment pour effacer l'écran, 'exit' pour quitter\n\n", style="dim")
            welcome_body.append("Astuce : Tapez une commande ou un chemin et appuyez sur [Tab] pour l'autocomplétion.", style="italic dim")
            panel_title = "[bold cyan]Bienvenue[/bold cyan]"
        else:
            welcome_body.append("⚡ COMMAND CENTER ", style="bold cyan")
            welcome_body.append("— Modern Terminal Workspace for Windows\n\n", style="bold white")
            welcome_body.append("Active Shell: ", style="bold")
            welcome_body.append(f"{self.shell.shell_type.upper()} ", style=f"bold {shell_badge_color}")
            welcome_body.append("• Location: ", style="dim")
            welcome_body.append(f"{self.shell.cwd}\n", style="dim cyan")
            if loc.is_git:
                welcome_body.append("• Git Repo: ", style="dim")
                welcome_body.append(f"{loc.repo_name} [{loc.branch}]\n\n", style="bold green")
            else:
                welcome_body.append(f"• Drive Root: {loc.root}\n\n", style="dim")
            welcome_body.append("Quick Start for Beginners:\n", style="bold white")
            welcome_body.append("  • Click any Quick Action button below (Files, Top Apps, Disks, Ping)\n", style="cyan")
            welcome_body.append("  • Press [Ctrl+L] to browse 86 everyday & specialized commands\n", style="cyan")
            welcome_body.append("  • Press [Ctrl+P] for fuzzy command palette & instant search\n", style="cyan")
            welcome_body.append("  • Type 'clear' or 'cls' anytime to wipe screen, 'exit' to close\n\n", style="dim")
            welcome_body.append("Pro Tip: Start typing any command or file name and press [Tab] for auto-completion.", style="italic dim")
            panel_title = "[bold cyan]Welcome[/bold cyan]"

        log.write(Panel(welcome_body, title=panel_title, border_style="cyan", padding=(0, 1)))

        inp = self.query_one("#command-input", Input)
        inp.placeholder = t("placeholder_ps", lang) if self.shell.shell_type == "powershell" else t("placeholder_cmd", lang)
        inp.focus()

    @on(Button.Pressed, "#qa-files")
    def on_qa_files(self) -> None:
        cmd = "Get-ChildItem" if self.shell.shell_type == "powershell" else "dir"
        self._execute_command(cmd)
        self.query_one("#command-input", Input).focus()

    @on(Button.Pressed, "#qa-procs")
    def on_qa_procs(self) -> None:
        cmd = "Get-Process | Sort-Object CPU -Descending | Select-Object -First 8" if self.shell.shell_type == "powershell" else "tasklist"
        self._execute_command(cmd)
        self.query_one("#command-input", Input).focus()

    @on(Button.Pressed, "#qa-disks")
    def on_qa_disks(self) -> None:
        cmd = "Get-Volume" if self.shell.shell_type == "powershell" else "wmic logicaldisk get caption,freespace,size"
        self._execute_command(cmd)
        self.query_one("#command-input", Input).focus()

    @on(Button.Pressed, "#qa-ping")
    def on_qa_ping(self) -> None:
        self._execute_command("ping -n 4 8.8.8.8")
        self.query_one("#command-input", Input).focus()

    @on(Button.Pressed, "#qa-library")
    def on_qa_library(self) -> None:
        self.action_open_library()

    @on(Button.Pressed, "#qa-shell")
    def on_qa_shell(self) -> None:
        self.action_toggle_shell()
        self.query_one("#command-input", Input).focus()

    @on(Button.Pressed, "#qa-clear")
    def on_qa_clear(self) -> None:
        self.query_one(RichLog).clear()
        self.query_one("#command-input", Input).focus()

    @on(Input.Submitted, "#command-input")
    def handle_command_submit(self, event: Input.Submitted) -> None:
        """Called when a command is submitted from the input line."""
        self._hide_suggestions()
        cmd = event.value.strip()
        if not cmd:
            return

        input_widget = self.query_one(Input)
        input_widget.value = ""

        # Built-in terminal commands
        cmd_lower = cmd.lower()
        if cmd_lower in ("cls", "clear"):
            self.query_one(RichLog).clear()
            return

        if cmd_lower == "cmd":
            if self.shell.shell_type != "cmd":
                self.action_toggle_shell()
            return

        if cmd_lower in ("powershell", "pwsh"):
            if self.shell.shell_type != "powershell":
                self.action_toggle_shell()
            return

        if cmd_lower in ("exit", "quit"):
            self.action_quit()
            return

        # Check safety if enabled
        if self.settings.safety_enabled:
            is_danger, reason = is_dangerous_command(cmd)
            if is_danger:
                self.push_screen(
                    SafetyConfirmationDialog(cmd, reason),
                    lambda confirmed: self._on_safety_confirm_result(confirmed, cmd),
                )
                return

        self._execute_command(cmd)

    def _on_safety_confirm_result(self, confirmed: bool, cmd: str) -> None:
        """Callback from dangerous command confirmation modal."""
        if confirmed:
            self._execute_command(cmd)
        else:
            log = self.query_one(RichLog)
            log.write(f"\n[dim yellow]> Cancelled dangerous command: {cmd}[/dim yellow]")
            self.query_one(Input).focus()

    def _execute_command(self, cmd: str) -> None:
        """Executes a validated command."""
        self.current_running_command = cmd

        # Track in history
        if not self.command_history or self.command_history[-1] != cmd:
            self.command_history.append(cmd)
        self.history_index = -1

        # Render command banner in output
        log = self.query_one(RichLog)
        safe_cmd = escape(cmd)
        prompt_arrow = "[bold cyan]❯[/bold cyan]" if self.shell.shell_type == "powershell" else "[bold yellow]❯[/bold yellow]"
        log.write(f"\n{prompt_arrow} [bold white]{safe_cmd}[/bold white]")

        # Update status
        self._set_state_running()

        # Execute off the UI thread
        self._active_run_id += 1
        self.run_command_in_background(cmd, self._active_run_id)

    @work(thread=True)
    def run_command_in_background(self, cmd: str, run_id: int) -> None:
        """Runs the command in the persistent shell worker thread."""
        current_buffer: List[str] = []
        current_bytes = 0

        def on_chunk(chunk: str) -> None:
            nonlocal current_bytes
            if current_bytes < 4096:
                current_buffer.append(chunk)
                current_bytes += len(chunk)
            self.call_from_thread(self._append_chunk, chunk)

        exit_code, new_cwd, duration_ms = self.shell.execute(cmd, on_output=on_chunk)
        self.call_from_thread(self._on_command_finished, exit_code, new_cwd, duration_ms, run_id, current_buffer)

    def _append_chunk(self, chunk: str) -> None:
        """Appends output chunks safely onto the RichLog widget."""
        log = self.query_one(RichLog)
        # Strip trailing newline because RichLog.write appends one
        clean_text = chunk.rstrip("\r\n")
        if clean_text:
            log.write(Text(clean_text))

    def _on_command_finished(
        self,
        exit_code: int,
        new_cwd: str,
        duration_ms: int,
        run_id: int = 0,
        output_buffer: Optional[List[str]] = None,
    ) -> None:
        """Updates the status and UI once command execution completes."""
        if run_id != self._active_run_id:
            return

        if output_buffer is not None:
            self.last_output_buffer = output_buffer

        log = self.query_one(RichLog)
        ec_color = "green" if exit_code == 0 else "red"
        ec_symbol = "✔" if exit_code == 0 else "✘"
        log.write(
            f"[dim]-- exit: [{ec_color}]{exit_code}[/{ec_color}] | {duration_ms}ms {ec_symbol}[/dim]"
        )

        # Log into SQLite history
        if self.current_running_command:
            preview = "" if self.settings.history_retention == "off" else "".join(self.last_output_buffer)
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
        status_state.update(t("status_ready", self.settings.language))

        status_cwd = self.query_one("#status-cwd", Static)
        status_cwd.update(f"{new_cwd}")

        loc = get_location_info(new_cwd)
        status_repo = self.query_one("#status-repo", Static)
        status_repo.update(loc.get_repo_badge(self.settings.language))

        prompt_sym = self.query_one("#prompt-symbol", Static)
        prompt_sym.update(self._render_prompt_symbol())

        # Update exit code badge
        exit_badge = self.query_one("#status-exit", Static)
        exit_lbl = t("status_exit", self.settings.language)
        if exit_code == 0:
            exit_badge.update(f"{exit_lbl}: [green]0[/green]")
        else:
            exit_badge.update(f"{exit_lbl}: [red]{exit_code}[/red]")

        self.query_one(Input).focus()

    def _set_state_running(self) -> None:
        """Set status bar to running state."""
        status_state = self.query_one("#status-state", Static)
        status_state.update(t("status_running", self.settings.language))

    @on(Input.Changed, "#command-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Trigger auto-suggest ranking as the user types."""
        if getattr(self, "_suppress_next_suggest", False):
            self._suppress_next_suggest = False
            self._hide_suggestions()
            return

        query = event.value.strip()
        if not query:
            self._hide_suggestions()
            return

        suggestions = rank_suggestions(query, self.shell.shell_type, cwd=self.shell.cwd)
        if not suggestions:
            self._hide_suggestions()
            return

        self.current_suggestions = suggestions
        sugg_list = self.query_one("#suggestions-list", OptionList)
        sugg_list.clear_options()

        for idx, s in enumerate(suggestions):
            source_badge = ""
            if s.source == "path":
                source_badge = "[cyan]PATH[/cyan] "
            elif s.source == "library":
                source_badge = "[green]LIB [/green] "
            elif s.source == "history":
                source_badge = "[yellow]HIST[/yellow] "

            fav_star = "[yellow]★ [/yellow]" if s.favorite else ""
            desc = f"  [dim]— {escape(s.description)}[/dim]" if s.description else ""
            prompt_text = f"{fav_star}{source_badge}{escape(s.command)}{desc}"
            sugg_list.add_option(Option(prompt_text, id=str(idx)))

        sugg_list.highlighted = 0
        self.query_one("#suggestions-container").add_class("visible")

    def _hide_suggestions(self) -> None:
        """Hides the suggestions dropdown."""
        try:
            container = self.query_one("#suggestions-container")
            container.remove_class("visible")
            self.query_one("#suggestions-list", OptionList).clear_options()
        except Exception:
            pass
        self.current_suggestions = []

    def _accept_suggestion(self, index: Optional[int] = None) -> None:
        """Accepts a suggestion and fills the input widget."""
        if not self.current_suggestions:
            return
        if index is None:
            sugg_list = self.query_one("#suggestions-list", OptionList)
            index = sugg_list.highlighted if sugg_list.highlighted is not None else 0

        if 0 <= index < len(self.current_suggestions):
            cmd = self.current_suggestions[index].command
            input_widget = self.query_one("#command-input", Input)
            self._suppress_next_suggest = True
            input_widget.value = cmd
            input_widget.cursor_position = len(cmd)
            self._hide_suggestions()
            input_widget.focus()

    @on(OptionList.OptionSelected, "#suggestions-list")
    def on_suggestion_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle mouse click or selection on suggestions list."""
        self._accept_suggestion(event.option_index)

    def on_key(self, event: events.Key) -> None:
        """Intercepts Tab, Esc, Up, Down when navigating suggestions."""
        input_widget = self.query_one("#command-input", Input)
        if not input_widget.has_focus:
            return

        sugg_container = self.query_one("#suggestions-container")
        is_sugg_visible = sugg_container.has_class("visible")

        if event.key == "tab":
            if is_sugg_visible and self.current_suggestions:
                event.prevent_default()
                event.stop()
                self._accept_suggestion()
        elif event.key == "escape":
            if is_sugg_visible:
                event.prevent_default()
                event.stop()
                self._hide_suggestions()
        elif event.key == "down":
            if is_sugg_visible:
                event.prevent_default()
                event.stop()
                sugg_list = self.query_one("#suggestions-list", OptionList)
                sugg_list.action_cursor_down()
        elif event.key == "up":
            if is_sugg_visible:
                event.prevent_default()
                event.stop()
                sugg_list = self.query_one("#suggestions-list", OptionList)
                sugg_list.action_cursor_up()

    def action_open_history(self) -> None:
        """Opens the History screen."""
        self.push_screen(HistoryScreen(), self._on_history_screen_result)

    def _on_history_screen_result(self, cmd: Optional[str]) -> None:
        """Callback when a command is selected from the History screen."""
        if cmd:
            self._suppress_next_suggest = True
            input_widget = self.query_one(Input)
            input_widget.value = cmd
            input_widget.focus()
            self.handle_command_submit(Input.Submitted(input_widget, cmd))

    def action_open_library(self) -> None:
        """Opens the Command Library screen (Ctrl+L)."""
        self.push_screen(LibraryScreen(), self._on_library_screen_result)

    def _on_library_screen_result(self, cmd: Optional[str]) -> None:
        """Callback when a command is selected to run from the Library screen."""
        if cmd:
            self._suppress_next_suggest = True
            input_widget = self.query_one(Input)
            input_widget.value = cmd
            input_widget.cursor_position = len(cmd)
            input_widget.focus()
            if self.settings.library_enter_action == "run":
                self.handle_command_submit(Input.Submitted(input_widget, cmd))

    def action_open_settings(self) -> None:
        """Opens the Settings configuration screen (F10)."""
        self.push_screen(SettingsScreen(self.settings), self._on_settings_result)

    def _on_settings_result(self, new_settings: Optional[AppSettings]) -> None:
        """Callback when settings are saved."""
        if new_settings:
            old_lang = self.settings.language
            self.settings = new_settings
            self.theme = new_settings.theme
            if new_settings.language != old_lang:
                self._refresh_ui_language()
            self.notify(t("settings_saved_notify", self.settings.language), timeout=2)

    def action_open_palette(self) -> None:
        """Opens the Command Palette and Help screen (Ctrl+P)."""
        self.push_screen(PaletteScreen(active_shell=self.shell.shell_type), self._on_palette_screen_result)

    def _on_palette_screen_result(self, result: Optional[Tuple[str, str]]) -> None:
        """Callback when an action is selected from the Command Palette."""
        if not result:
            return
        action, cmd = result
        self._suppress_next_suggest = True
        input_widget = self.query_one(Input)
        input_widget.value = cmd
        input_widget.cursor_position = len(cmd)
        input_widget.focus()

        if action == "run":
            self.handle_command_submit(Input.Submitted(input_widget, cmd))

    def action_toggle_shell(self) -> None:
        """Toggles active shell between PowerShell and CMD with F2."""
        new_shell = self.shell_manager.toggle()
        shell_name = "PowerShell" if new_shell == "powershell" else "Command Prompt (CMD)"
        log = self.query_one(RichLog)
        log.write(f"\n[dim]-- Switched active shell to [bold cyan]{shell_name}[/bold cyan] --[/dim]")

        # Update prompt symbol
        self.query_one("#prompt-symbol", Static).update(self._render_prompt_symbol())

        # Update header status
        prompt_color = "cyan" if new_shell == "powershell" else "yellow"
        self.query_one("#header-hints", Label).update(
            f"[bold {prompt_color}]{new_shell.upper()}[/bold {prompt_color}]  •  [dim]{t('header_settings', self.settings.language)}[/dim]"
        )

        # Update status bar
        status_shell = self.query_one("#status-shell", Static)
        status_shell.update(f"{new_shell.upper()}")

        status_cwd = self.query_one("#status-cwd", Static)
        status_cwd.update(f"{self.shell.cwd}")

        loc = get_location_info(self.shell.cwd)
        status_repo = self.query_one("#status-repo", Static)
        status_repo.update(loc.get_repo_badge(self.settings.language))

        # Update input placeholder
        inp = self.query_one("#command-input", Input)
        inp.placeholder = t("placeholder_ps", self.settings.language) if new_shell == "powershell" else t("placeholder_cmd", self.settings.language)

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
            self._active_run_id += 1
            self.shell.interrupt()
            log = self.query_one(RichLog)
            log.write("[bold yellow]^C (Interrupted / Session Reset)[/bold yellow]")
            self._on_command_finished(130, self.shell.cwd, 0, self._active_run_id, self.last_output_buffer)
        elif input_widget.value:
            input_widget.value = ""

    def action_restart_shell(self) -> None:
        """Explicitly restarts the persistent shell session."""
        self.shell.restart()
        log = self.query_one(RichLog)
        log.write("[bold yellow]Shell session restarted.[/bold yellow]")
        loc = get_location_info(self.shell.cwd)
        self.query_one("#status-cwd", Static).update(f"{self.shell.cwd}")
        self.query_one("#status-repo", Static).update(loc.get_repo_badge(self.settings.language))
        self.query_one("#prompt-symbol", Static).update(self._render_prompt_symbol())
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
        try:
            if self.query_one("#suggestions-container").has_class("visible"):
                return
        except Exception:
            pass
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
        try:
            if self.query_one("#suggestions-container").has_class("visible"):
                return
        except Exception:
            pass
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
