"""Command Palette and Help Screen (Ctrl+P) for Command Center."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from rich.markup import escape
from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, OptionList, RichLog
from textual.widgets.option_list import Option

from command_center.library import get_library_entries


class PaletteScreen(ModalScreen[Optional[Tuple[str, str]]]):
    """Fuzzy search command palette and help browser."""

    BINDINGS = [
        Binding("escape", "dismiss_palette", "Close", show=True),
        Binding("tab", "insert", "Insert to Input", show=True),
        Binding("enter", "run", "Run", show=True),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
    ]

    def __init__(self, active_shell: str = "powershell", **kwargs) -> None:
        super().__init__(**kwargs)
        self.active_shell = active_shell
        self.entries: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-dialog"):
            yield Label("COMMAND PALETTE & HELP", id="palette-title")
            yield Input(
                placeholder="Type to search all commands, descriptions, or tags... (Enter=Run, Tab=Insert)",
                id="palette-search",
            )
            yield OptionList(id="palette-list")
            with Container(id="palette-detail-container"):
                yield RichLog(id="palette-detail-log", wrap=True, highlight=True)
            yield Label("[Enter] Run Command  •  [Tab] Insert into Input  •  [Esc] Close", id="palette-hint")

    def on_mount(self) -> None:
        self.refresh_results()
        self.query_one("#palette-search", Input).focus()

    def refresh_results(self) -> None:
        search_term = self.query_one("#palette-search", Input).value.strip()
        self.entries = get_library_entries(
            search=search_term,
            shell=self.active_shell,
            limit=50,
        )

        option_list = self.query_one("#palette-list", OptionList)
        option_list.clear_options()

        for idx, entry in enumerate(self.entries):
            fav_marker = "[yellow]*[/yellow] " if entry["favorite"] else ""
            desc = f" [dim]-- {escape(entry['description'])}[/dim]" if entry.get("description") else ""
            prompt = f"{fav_marker}[bold]{escape(entry['name'])}[/bold]: [cyan]{escape(entry['command'])}[/cyan]{desc}"
            option_list.add_option(Option(prompt, id=str(idx)))

        if self.entries:
            option_list.highlighted = 0
            self.update_detail_at_index(0)
        else:
            self.query_one("#palette-detail-log", RichLog).clear()

    @on(Input.Changed, "#palette-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.refresh_results()

    @on(OptionList.OptionHighlighted, "#palette-list")
    def on_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self.update_detail_at_index(event.option_index)

    @on(OptionList.OptionSelected, "#palette-list")
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if 0 <= event.option_index < len(self.entries):
            cmd = self.entries[event.option_index]["command"]
            self.dismiss(("run", cmd))

    def update_detail_at_index(self, index: int) -> None:
        log = self.query_one("#palette-detail-log", RichLog)
        log.clear()
        if 0 <= index < len(self.entries):
            item = self.entries[index]
            log.write(f"[bold cyan]{escape(item['name'])}[/bold cyan] [dim]({item['category']} • {item['shell'].upper()})[/dim]")
            log.write(f"[bold white]> {escape(item['command'])}[/bold white]")
            if item.get("description"):
                log.write(f"[dim]Description:[/dim] {escape(item['description'])}")
            if item.get("example"):
                log.write(f"[dim]Example:[/dim] [cyan]{escape(item['example'])}[/cyan]")
            if item.get("tags"):
                log.write(f"[dim]Tags:[/dim] {escape(item['tags'])}")

    def action_dismiss_palette(self) -> None:
        self.dismiss(None)

    def action_run(self) -> None:
        option_list = self.query_one("#palette-list", OptionList)
        idx = option_list.highlighted if option_list.highlighted is not None else 0
        if 0 <= idx < len(self.entries):
            cmd = self.entries[idx]["command"]
            self.dismiss(("run", cmd))

    def action_insert(self) -> None:
        option_list = self.query_one("#palette-list", OptionList)
        idx = option_list.highlighted if option_list.highlighted is not None else 0
        if 0 <= idx < len(self.entries):
            cmd = self.entries[idx]["command"]
            self.dismiss(("insert", cmd))

    def action_cursor_down(self) -> None:
        self.query_one("#palette-list", OptionList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#palette-list", OptionList).action_cursor_up()

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation directly from search input."""
        if event.key == "tab":
            event.prevent_default()
            event.stop()
            self.action_insert()
        elif event.key == "enter":
            event.prevent_default()
            event.stop()
            self.action_run()
        elif event.key == "down":
            event.prevent_default()
            event.stop()
            self.action_cursor_down()
        elif event.key == "up":
            event.prevent_default()
            event.stop()
            self.action_cursor_up()
