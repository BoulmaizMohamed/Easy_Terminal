"""Repository Navigator Screen (Ctrl+G) for Command Center."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.markup import escape
from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option

from command_center.git_info import get_known_repositories, get_location_info
from command_center.i18n import t


class RepoScreen(ModalScreen[Optional[str]]):
    """Modal screen to search and quickly jump between Git repositories."""

    BINDINGS = [
        Binding("escape", "cancel", "Close", show=True),
        Binding("enter", "select_repo", "Navigate", show=True),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
    ]

    def __init__(self, current_cwd: Optional[str] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_cwd = current_cwd
        self.all_repos: List[Dict[str, Any]] = []
        self.filtered_repos: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        lang_obj = getattr(getattr(self, "app", None), "settings", None)
        lang = getattr(lang_obj, "language", "en") if lang_obj else "en"

        with Vertical(id="repo-dialog"):
            yield Label(t("repo_dialog_title", lang), id="repo-title")
            yield Input(
                placeholder=t("repo_search_placeholder", lang),
                id="repo-search",
            )
            yield OptionList(id="repo-list")
            yield Label(t("repo_dialog_hint", lang), id="repo-hint")

    def on_mount(self) -> None:
        self.all_repos = get_known_repositories(cwd=self.current_cwd)
        self.refresh_list("")
        self.query_one("#repo-search", Input).focus()

    def refresh_list(self, query: str = "") -> None:
        """Filters and populates the option list with repositories."""
        q = query.strip().lower()
        if not q:
            self.filtered_repos = list(self.all_repos)
        else:
            self.filtered_repos = [
                r
                for r in self.all_repos
                if q in r["name"].lower() or q in r["path"].lower() or q in r.get("branch", "").lower()
            ]

        lang_obj = getattr(getattr(self, "app", None), "settings", None)
        lang = getattr(lang_obj, "language", "en") if lang_obj else "en"
        current_loc = get_location_info(self.current_cwd)

        option_list = self.query_one("#repo-list", OptionList)
        option_list.clear_options()

        for idx, repo in enumerate(self.filtered_repos):
            is_current = False
            if current_loc.is_git and current_loc.repo_root:
                try:
                    is_current = Path(repo["path"]).resolve() == Path(current_loc.repo_root).resolve()
                except Exception:
                    pass

            active_tag = f"[bold green]{t('repo_active_badge', lang)}[/bold green] " if is_current else ""
            branch_str = f" [dim green]({escape(repo['branch'])})[/dim green]" if repo.get("branch") else ""
            item_text = (
                f"{active_tag}[bold cyan]{escape(repo['name'])}[/bold cyan]"
                f"{branch_str} [dim]• {escape(repo['path'])}[/dim]"
            )
            option_list.add_option(Option(item_text, id=str(idx)))

        if self.filtered_repos:
            option_list.highlighted = 0

    @on(Input.Changed, "#repo-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.refresh_list(event.value)

    @on(Input.Submitted, "#repo-search")
    def on_search_submitted(self) -> None:
        self.action_select_repo()

    @on(OptionList.OptionSelected, "#repo-list")
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.option_index < len(self.filtered_repos):
            self.dismiss(self.filtered_repos[event.option_index]["path"])

    def action_select_repo(self) -> None:
        option_list = self.query_one("#repo-list", OptionList)
        idx = option_list.highlighted
        if idx is not None and 0 <= idx < len(self.filtered_repos):
            self.dismiss(self.filtered_repos[idx]["path"])

    def action_cursor_down(self) -> None:
        self.query_one("#repo-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#repo-list", OptionList).action_cursor_up()

    def action_cancel(self) -> None:
        self.dismiss(None)
