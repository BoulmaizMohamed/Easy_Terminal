"""Command Library Screen for Command Center."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pyperclip
from rich.markup import escape
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label, RichLog, Static

from command_center.importers.json_sync import export_library_json, import_library_json
from command_center.importers.tldr import sync_tldr_pages
from command_center.library import (
    add_library_entry,
    delete_library_entry,
    get_categories,
    get_library_entries,
    toggle_favorite,
    update_library_entry,
)


class CommandEditorDialog(ModalScreen[Optional[Dict[str, Any]]]):
    """Modal dialog for creating or editing a command library entry."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, entry: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry = entry

    def compose(self) -> ComposeResult:
        is_edit = self.entry is not None
        title = "EDIT COMMAND" if is_edit else "ADD COMMAND TO LIBRARY"

        with Vertical(id="editor-dialog"):
            yield Label(title, id="editor-title")

            yield Label("Name:", classes="field-label")
            yield Input(
                value=self.entry.get("name", "") if self.entry else "",
                placeholder="e.g. Check Open Ports",
                id="field-name",
            )

            yield Label("Command:", classes="field-label")
            yield Input(
                value=self.entry.get("command", "") if self.entry else "",
                placeholder="e.g. netstat -ano",
                id="field-command",
            )

            with Horizontal(classes="editor-row"):
                with Vertical(classes="half-col"):
                    yield Label("Shell (powershell / cmd / both):", classes="field-label")
                    yield Input(
                        value=self.entry.get("shell", "both") if self.entry else "both",
                        placeholder="both",
                        id="field-shell",
                    )
                with Vertical(classes="half-col"):
                    yield Label("Category:", classes="field-label")
                    yield Input(
                        value=self.entry.get("category", "General") if self.entry else "General",
                        placeholder="e.g. Network",
                        id="field-category",
                    )

            yield Label("Description:", classes="field-label")
            yield Input(
                value=self.entry.get("description", "") if self.entry else "",
                placeholder="What this command does...",
                id="field-desc",
            )

            yield Label("Example:", classes="field-label")
            yield Input(
                value=self.entry.get("example", "") if self.entry else "",
                placeholder="Example usage...",
                id="field-example",
            )

            yield Label("Tags (comma-separated):", classes="field-label")
            yield Input(
                value=self.entry.get("tags", "") if self.entry else "",
                placeholder="network, ports, tcp",
                id="field-tags",
            )

            with Horizontal(id="editor-actions"):
                yield Button("Save", variant="primary", id="btn-save")
                yield Button("Cancel", id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#field-name", Input).focus()

    @on(Button.Pressed, "#btn-save")
    def on_save_pressed(self) -> None:
        name = self.query_one("#field-name", Input).value.strip()
        cmd = self.query_one("#field-command", Input).value.strip()
        shell = self.query_one("#field-shell", Input).value.strip().lower() or "both"
        category = self.query_one("#field-category", Input).value.strip() or "General"
        desc = self.query_one("#field-desc", Input).value.strip()
        example = self.query_one("#field-example", Input).value.strip()
        tags = self.query_one("#field-tags", Input).value.strip()

        if not name or not cmd:
            self.notify("Name and Command are required!", severity="error")
            return

        result = {
            "name": name,
            "command": cmd,
            "shell": shell if shell in ("cmd", "powershell", "both") else "both",
            "category": category,
            "description": desc,
            "example": example,
            "tags": tags,
        }
        self.dismiss(result)

    @on(Button.Pressed, "#btn-cancel")
    def on_cancel_pressed(self) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class LibraryScreen(ModalScreen[Optional[str]]):
    """Full-featured Command Library table with filtering, sorting, and editing."""

    BINDINGS = [
        Binding("escape", "dismiss_screen", "Close", show=True),
        Binding("enter", "run_selected", "Run", show=True),
        Binding("a", "add", "Add", show=True),
        Binding("e", "edit", "Edit", show=True),
        Binding("f", "toggle_fav", "Favorite", show=True),
        Binding("s", "sync_tldr", "Sync tldr", show=True),
        Binding("x", "export", "Export", show=True),
        Binding("i", "import", "Import", show=True),
        Binding("delete", "delete", "Delete", show=True),
        Binding("c", "copy", "Copy", show=True),
    ]

    SORTS = ["most_used", "alphabetical", "category", "favorites_first", "recently_used", "newest"]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rows_cache: Dict[str, Dict[str, Any]] = {}
        self.sort_index: int = 0
        self.filter_category: Optional[str] = None
        self.filter_shell: Optional[str] = None
        self.filter_favorites: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="library-dialog"):
            with Horizontal(id="library-header"):
                yield Label("COMMAND LIBRARY", id="library-title")
                yield Input(
                    placeholder="Search library by name, command, description, or tags... (Esc to close)",
                    id="library-search",
                )

            with Horizontal(id="library-filter-bar"):
                yield Button("All Shells", id="btn-shell-all", classes="lib-filter-btn active")
                yield Button("PowerShell", id="btn-shell-ps", classes="lib-filter-btn")
                yield Button("CMD", id="btn-shell-cmd", classes="lib-filter-btn")
                yield Button("Favorites Only", id="btn-filter-favs", classes="lib-filter-btn")
                yield Button(f"Sort: {self.current_sort_label}", id="btn-sort-cycle", classes="lib-filter-btn")
                yield Button("Sync tldr (s)", id="btn-sync-tldr", classes="lib-filter-btn")
                yield Button("Export (x)", id="btn-export-json", classes="lib-filter-btn")
                yield Button("Import (i)", id="btn-import-json", classes="lib-filter-btn")
                yield Button("+ Add (a)", variant="success", id="btn-add-command")

            with Container(id="library-table-container"):
                yield DataTable(id="library-table", cursor_type="row")

            with Container(id="library-detail-container"):
                yield Label("Command Details", id="library-detail-title")
                yield RichLog(id="library-detail-log", wrap=True, highlight=True)

            yield Footer()

    @property
    def current_sort(self) -> str:
        return self.SORTS[self.sort_index]

    @property
    def current_sort_label(self) -> str:
        return self.current_sort.replace("_", " ").title()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Fav", "Name", "Command", "Shell", "Category", "Uses")
        self.refresh_table()
        self.query_one("#library-search", Input).focus()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        self.rows_cache.clear()
        search_term = self.query_one("#library-search", Input).value.strip()

        entries = get_library_entries(
            search=search_term,
            category=self.filter_category,
            shell=self.filter_shell,
            favorites_only=self.filter_favorites,
            sort_by=self.current_sort,
            limit=250,
        )

        for entry in entries:
            row_key = str(entry["id"])
            self.rows_cache[row_key] = entry
            fav_icon = "[yellow]*[/yellow]" if entry["favorite"] else "-"
            table.add_row(
                fav_icon,
                escape(entry["name"]),
                escape(entry["command"]),
                entry["shell"].upper(),
                entry["category"],
                str(entry["use_count"]),
                key=row_key,
            )

        if table.row_count > 0:
            first_key = list(self.rows_cache.keys())[0]
            self.update_detail_for_key(first_key)
        else:
            self.query_one("#library-detail-log", RichLog).clear()

    @on(Input.Changed, "#library-search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.refresh_table()

    @on(Button.Pressed, "#btn-shell-all")
    def filter_all_shells(self) -> None:
        self.filter_shell = None
        self._update_btn_active("btn-shell-all")
        self.refresh_table()

    @on(Button.Pressed, "#btn-shell-ps")
    def filter_ps_shell(self) -> None:
        self.filter_shell = "powershell"
        self._update_btn_active("btn-shell-ps")
        self.refresh_table()

    @on(Button.Pressed, "#btn-shell-cmd")
    def filter_cmd_shell(self) -> None:
        self.filter_shell = "cmd"
        self._update_btn_active("btn-shell-cmd")
        self.refresh_table()

    @on(Button.Pressed, "#btn-filter-favs")
    def toggle_favs_filter(self) -> None:
        self.filter_favorites = not self.filter_favorites
        btn = self.query_one("#btn-filter-favs", Button)
        if self.filter_favorites:
            btn.add_class("active")
        else:
            btn.remove_class("active")
        self.refresh_table()

    @on(Button.Pressed, "#btn-sort-cycle")
    def cycle_sort(self) -> None:
        self.sort_index = (self.sort_index + 1) % len(self.SORTS)
        self.query_one("#btn-sort-cycle", Button).label = f"Sort: {self.current_sort_label}"
        self.refresh_table()

    @on(Button.Pressed, "#btn-sync-tldr")
    def on_sync_button_pressed(self) -> None:
        self.action_sync_tldr()

    @on(Button.Pressed, "#btn-export-json")
    def on_export_button_pressed(self) -> None:
        self.action_export()

    @on(Button.Pressed, "#btn-import-json")
    def on_import_button_pressed(self) -> None:
        self.action_import()

    @on(Button.Pressed, "#btn-add-command")
    def on_add_button_pressed(self) -> None:
        self.action_add()

    def _update_btn_active(self, active_id: str) -> None:
        for btn_id in ("btn-shell-all", "btn-shell-ps", "btn-shell-cmd"):
            btn = self.query_one(f"#{btn_id}", Button)
            if btn_id == active_id:
                btn.add_class("active")
            else:
                btn.remove_class("active")

    @on(DataTable.RowHighlighted, "#library-table")
    def on_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value:
            self.update_detail_for_key(event.row_key.value)

    @on(DataTable.RowSelected, "#library-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key and event.row_key.value:
            entry = self.rows_cache.get(event.row_key.value)
            if entry:
                self.dismiss(entry["command"])

    def update_detail_for_key(self, key: str) -> None:
        entry = self.rows_cache.get(key)
        detail_log = self.query_one("#library-detail-log", RichLog)
        detail_log.clear()
        if not entry:
            return

        detail_log.write(f"[bold cyan]{escape(entry['name'])}[/bold cyan] [dim]({entry['shell'].upper()} • {entry['category']})[/dim]")
        detail_log.write(f"[bold white]> {escape(entry['command'])}[/bold white]")
        if entry.get("description"):
            detail_log.write(f"[dim]Description:[/dim] {escape(entry['description'])}")
        if entry.get("example"):
            detail_log.write(f"[dim]Example:[/dim] [cyan]{escape(entry['example'])}[/cyan]")
        if entry.get("tags"):
            detail_log.write(f"[dim]Tags:[/dim] {escape(entry['tags'])}")

    def get_selected_entry(self) -> Optional[Dict[str, Any]]:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            keys = list(self.rows_cache.keys())
            if 0 <= table.cursor_row < len(keys):
                return self.rows_cache.get(keys[table.cursor_row])
        return None

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def action_run_selected(self) -> None:
        entry = self.get_selected_entry()
        if entry:
            self.dismiss(entry["command"])

    def action_copy(self) -> None:
        entry = self.get_selected_entry()
        if entry:
            pyperclip.copy(entry["command"])
            self.notify(f"Copied: {entry['command']}", timeout=2)

    def action_toggle_fav(self) -> None:
        entry = self.get_selected_entry()
        if entry:
            new_state = toggle_favorite(entry["id"])
            entry["favorite"] = 1 if new_state else 0
            self.notify(f"{'* Favorited' if new_state else 'Unfavorited'}: {entry['name']}", timeout=1)
            self.refresh_table()

    @work(thread=True)
    def action_sync_tldr(self) -> None:
        """Synchronizes tldr-pages from the official repository."""
        self.notify("Syncing tldr-pages in background...", timeout=3)
        try:
            added, updated = sync_tldr_pages()
            self.call_from_thread(self._on_sync_finished, added, updated)
        except Exception as e:
            self.notify(f"Sync error: {e}", severity="error", timeout=5)

    def _on_sync_finished(self, added: int, updated: int) -> None:
        self.notify(f"tldr sync complete: {added} added, {updated} updated!", timeout=4)
        self.refresh_table()

    def action_export(self) -> None:
        """Exports user library entries to library_export.json."""
        dest = "library_export.json"
        try:
            count = export_library_json(dest, user_only=True)
            self.notify(f"Exported {count} user commands to {dest}", timeout=4)
        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error", timeout=4)

    def action_import(self) -> None:
        """Imports library entries from library_export.json."""
        src = "library_export.json"
        try:
            added, skipped = import_library_json(src)
            self.notify(f"Imported {added} commands ({skipped} duplicates skipped)", timeout=4)
            self.refresh_table()
        except FileNotFoundError:
            self.notify(f"File not found: {src} (export first or place file here)", severity="warning", timeout=4)
        except Exception as e:
            self.notify(f"Import failed: {e}", severity="error", timeout=4)

    def action_add(self) -> None:
        def on_add_result(data: Optional[Dict[str, Any]]) -> None:
            if data:
                add_library_entry(
                    name=data["name"],
                    command=data["command"],
                    shell=data["shell"],
                    category=data["category"],
                    description=data["description"],
                    example=data["example"],
                    tags=data["tags"],
                )
                self.notify(f"Added '{data['name']}' to library!", timeout=2)
                self.refresh_table()

        self.app.push_screen(CommandEditorDialog(), on_add_result)

    def action_edit(self) -> None:
        entry = self.get_selected_entry()
        if not entry:
            return

        def on_edit_result(data: Optional[Dict[str, Any]]) -> None:
            if data:
                update_library_entry(
                    entry_id=entry["id"],
                    name=data["name"],
                    command=data["command"],
                    shell=data["shell"],
                    category=data["category"],
                    description=data["description"],
                    example=data["example"],
                    tags=data["tags"],
                    favorite=bool(entry.get("favorite", False)),
                )
                self.notify(f"Updated '{data['name']}'!", timeout=2)
                self.refresh_table()

        self.app.push_screen(CommandEditorDialog(entry=entry), on_edit_result)

    def action_delete(self) -> None:
        entry = self.get_selected_entry()
        if not entry:
            return

        if entry.get("source") != "user":
            self.notify("Default seed commands cannot be deleted (only user commands).", severity="warning")
            return

        delete_library_entry(entry["id"], force=False)
        self.notify(f"Deleted '{entry['name']}'", timeout=2)
        self.refresh_table()
