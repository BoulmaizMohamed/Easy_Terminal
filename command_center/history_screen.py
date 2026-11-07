"""Command History Screen for Command Center."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pyperclip
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, RichLog, Static

from command_center.db import get_connection
from command_center.history import get_history, get_most_used


class HistoryScreen(ModalScreen[Optional[str]]):
    """Searchable command history table with filters and preview."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Close", show=True),
        Binding("enter", "run_selected", "Re-run", show=True),
        Binding("c", "copy_selected", "Copy", show=True),
        Binding("s", "save_to_library", "Save to Library", show=True),
        Binding("f", "focus_search", "Search", show=True),
        Binding("tab", "switch_focus", "Next Focus", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rows_cache: Dict[str, Dict[str, Any]] = {}
        self.filter_failed_only: bool = False
        self.view_most_used: bool = False
        self.filter_shell: Optional[str] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="history-dialog"):
            with Horizontal(id="history-header"):
                yield Label("COMMAND HISTORY", id="history-title")
                yield Input(
                    placeholder="Search history... (Type to filter, Esc to close)",
                    id="history-search",
                )

            with Horizontal(id="history-filter-bar"):
                yield Button("All", id="btn-filter-all", classes="filter-btn active")
                yield Button("Failed Only", id="btn-filter-failed", classes="filter-btn")
                yield Button("Top 25 Most Used", id="btn-filter-most-used", classes="filter-btn")
                yield Button("PowerShell", id="btn-filter-ps", classes="filter-btn")
                yield Button("CMD", id="btn-filter-cmd", classes="filter-btn")

            with Container(id="history-table-container"):
                yield DataTable(id="history-table", cursor_type="row")

            with Container(id="history-preview-container"):
                yield Label("Output Preview", id="history-preview-title")
                yield RichLog(id="history-preview-log", wrap=True, highlight=True)

            yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Time (UTC)", "Shell", "Command", "Exit", "Duration")
        self.refresh_table()
        self.query_one("#history-search", Input).focus()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        self.rows_cache.clear()
        search_term = self.query_one("#history-search", Input).value.strip()

        if self.view_most_used:
            entries = get_most_used(limit=25, shell=self.filter_shell)
            for idx, entry in enumerate(entries):
                row_key = f"most_{idx}"
                self.rows_cache[row_key] = entry
                time_str = entry["last_ran"][:19].replace("T", " ") if entry.get("last_ran") else "-"
                cmd_str = entry["command"]
                cnt_str = f"{entry['count']} runs"
                table.add_row(
                    time_str,
                    entry["shell"],
                    cmd_str,
                    "-",
                    cnt_str,
                    key=row_key,
                )
        else:
            entries = get_history(
                search=search_term,
                shell=self.filter_shell,
                failed_only=self.filter_failed_only,
                limit=150,
            )
            for entry in entries:
                row_key = str(entry["id"])
                self.rows_cache[row_key] = entry
                time_str = entry["ran_at"][:19].replace("T", " ") if entry.get("ran_at") else "-"
                exit_str = "0" if entry["exit_code"] == 0 else f"[red]{entry['exit_code']}[/red]"
                table.add_row(
                    time_str,
                    entry["shell"],
                    entry["command"],
                    exit_str,
                    f"{entry['duration_ms']}ms",
                    key=row_key,
                )

        if table.row_count > 0:
            first_key = list(self.rows_cache.keys())[0]
            self.update_preview_for_key(first_key)
        else:
            self.query_one("#history-preview-log", RichLog).clear()

    @on(Input.Changed, "#history-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-all")
    def filter_all(self) -> None:
        self.view_most_used = False
        self.filter_failed_only = False
        self.filter_shell = None
        self._update_button_classes("btn-filter-all")
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-failed")
    def filter_failed(self) -> None:
        self.view_most_used = False
        self.filter_failed_only = True
        self._update_button_classes("btn-filter-failed")
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-most-used")
    def filter_most_used(self) -> None:
        self.view_most_used = True
        self.filter_failed_only = False
        self._update_button_classes("btn-filter-most-used")
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-ps")
    def filter_ps(self) -> None:
        self.filter_shell = "powershell"
        self._update_button_classes("btn-filter-ps")
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-cmd")
    def filter_cmd(self) -> None:
        self.filter_shell = "cmd"
        self._update_button_classes("btn-filter-cmd")
        self.refresh_table()

    def _update_button_classes(self, active_id: str) -> None:
        for btn in self.query(".filter-btn"):
            if btn.id == active_id:
                btn.add_class("active")
            else:
                btn.remove_class("active")

    @on(DataTable.RowHighlighted, "#history-table")
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value:
            self.update_preview_for_key(event.row_key.value)

    @on(DataTable.RowSelected, "#history-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key and event.row_key.value:
            entry = self.rows_cache.get(event.row_key.value)
            if entry:
                self.dismiss(entry["command"])

    def update_preview_for_key(self, key: str) -> None:
        entry = self.rows_cache.get(key)
        preview_log = self.query_one("#history-preview-log", RichLog)
        preview_log.clear()
        if not entry:
            return

        cmd = entry.get("command", "")
        preview = entry.get("output_preview", "")
        preview_log.write(f"[bold cyan]Command:[/bold cyan] {cmd}")
        if preview:
            preview_log.write("[dim]Preview output:[/dim]")
            preview_log.write(preview.strip())
        else:
            preview_log.write("[dim](No output recorded)[/dim]")

    def get_selected_command(self) -> Optional[str]:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            row_keys = list(self.rows_cache.keys())
            if 0 <= table.cursor_row < len(row_keys):
                key = row_keys[table.cursor_row]
                entry = self.rows_cache.get(key)
                if entry:
                    return entry["command"]
        return None

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def action_run_selected(self) -> None:
        cmd = self.get_selected_command()
        if cmd:
            self.dismiss(cmd)

    def action_copy_selected(self) -> None:
        cmd = self.get_selected_command()
        if cmd:
            pyperclip.copy(cmd)
            self.notify("Command copied to clipboard!", timeout=2)

    def action_save_to_library(self) -> None:
        cmd = self.get_selected_command()
        if not cmd:
            return

        # Pre-populate library entry
        now = datetime.utcnow().isoformat()
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO library (name, command, shell, category, source, date_added, updated_at)
                    VALUES (?, ?, 'both', 'History', 'user', ?, ?)
                    ON CONFLICT(command, shell, source) DO NOTHING
                    """,
                    (cmd[:50], cmd, now, now),
                )
            self.notify(f"Saved '{cmd[:30]}...' to Library!", timeout=2)
        except Exception as e:
            self.notify(f"Could not save: {e}", severity="error")
        finally:
            conn.close()

    def action_focus_search(self) -> None:
        self.query_one("#history-search", Input).focus()
