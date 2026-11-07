"""Command library management, CRUD, sorting, and seed loading."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from command_center.db import get_connection

SEED_FILE_PATH = Path(__file__).parent / "data" / "seed_library.json"

SORT_OPTIONS = {
    "most_used": "use_count DESC, name ASC",
    "recently_used": "last_used_at DESC NULLS LAST, use_count DESC",
    "alphabetical": "name ASC",
    "category": "category ASC, name ASC",
    "favorites_first": "favorite DESC, use_count DESC, name ASC",
    "newest": "date_added DESC",
}


def load_seed_library(db_path: Optional[str | Path] = None) -> int:
    """
    Loads seed commands from data/seed_library.json into SQLite.
    Never overwrites user-created entries. Returns count of newly inserted rows.
    """
    if not SEED_FILE_PATH.exists():
        return 0

    with open(SEED_FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    inserted = 0

    with conn:
        for item in data:
            cursor = conn.execute(
                """
                INSERT INTO library (name, command, shell, category, description, example, tags, favorite, use_count, source, date_added, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'seed', ?, ?)
                ON CONFLICT(command, shell, source) DO NOTHING
                """,
                (
                    item["name"],
                    item["command"],
                    item.get("shell", "both").lower(),
                    item.get("category", "General"),
                    item.get("description", ""),
                    item.get("example", ""),
                    item.get("tags", ""),
                    now,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                inserted += 1

    conn.close()
    return inserted


def get_library_entries(
    search: str = "",
    category: Optional[str] = None,
    shell: Optional[str] = None,
    favorites_only: bool = False,
    source: Optional[str] = None,
    sort_by: str = "most_used",
    ascending: bool = False,
    limit: int = 200,
    offset: int = 0,
    db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieves sorted and filtered commands from the library."""
    conn = get_connection(db_path)
    query = "SELECT id, name, command, shell, category, description, example, tags, favorite, use_count, last_used_at, source, date_added, updated_at FROM library WHERE 1=1"
    params: List[Any] = []

    if search.strip():
        term = f"%{search.strip()}%"
        query += " AND (name LIKE ? OR command LIKE ? OR description LIKE ? OR tags LIKE ?)"
        params.extend([term, term, term, term])

    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category)

    if shell and shell.lower() != "all":
        query += " AND (shell = ? OR shell = 'both')"
        params.append(shell.lower())

    if favorites_only:
        query += " AND favorite = 1"

    if source and source.lower() != "all":
        query += " AND source = ?"
        params.append(source.lower())

    # Sort order
    order_clause = SORT_OPTIONS.get(sort_by, "use_count DESC, name ASC")
    if ascending:
        # Swap DESC and ASC
        order_clause = order_clause.replace("DESC", "__TMP__").replace("ASC", "DESC").replace("__TMP__", "ASC")

    query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def add_library_entry(
    name: str,
    command: str,
    shell: str = "both",
    category: str = "General",
    description: str = "",
    example: str = "",
    tags: str = "",
    favorite: bool = False,
    source: str = "user",
    db_path: Optional[str | Path] = None,
) -> int:
    """Adds a new command entry to the library."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO library (name, command, shell, category, description, example, tags, favorite, use_count, source, date_added, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                name.strip(),
                command.strip(),
                shell.lower(),
                category.strip() or "General",
                description.strip(),
                example.strip(),
                tags.strip(),
                1 if favorite else 0,
                source,
                now,
                now,
            ),
        )
        row_id = cursor.lastrowid or 0
    conn.close()
    return row_id


def update_library_entry(
    entry_id: int,
    name: str,
    command: str,
    shell: str,
    category: str,
    description: str,
    example: str,
    tags: str,
    favorite: bool,
    db_path: Optional[str | Path] = None,
) -> bool:
    """Updates an existing library entry."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            UPDATE library
            SET name = ?, command = ?, shell = ?, category = ?, description = ?,
                example = ?, tags = ?, favorite = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                command.strip(),
                shell.lower(),
                category.strip() or "General",
                description.strip(),
                example.strip(),
                tags.strip(),
                1 if favorite else 0,
                now,
                entry_id,
            ),
        )
        success = cursor.rowcount > 0
    conn.close()
    return success


def delete_library_entry(
    entry_id: int,
    force: bool = False,
    db_path: Optional[str | Path] = None,
) -> bool:
    """
    Deletes a library entry. By default only allows deleting source='user' entries.
    """
    conn = get_connection(db_path)
    with conn:
        if force:
            cursor = conn.execute("DELETE FROM library WHERE id = ?", (entry_id,))
        else:
            cursor = conn.execute("DELETE FROM library WHERE id = ? AND source = 'user'", (entry_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def toggle_favorite(entry_id: int, db_path: Optional[str | Path] = None) -> bool:
    """Toggles the favorite status of a command in the library."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            """
            UPDATE library
            SET favorite = CASE WHEN favorite = 1 THEN 0 ELSE 1 END,
                updated_at = ?
            WHERE id = ?
            """,
            (now, entry_id),
        )
        row = conn.execute("SELECT favorite FROM library WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return bool(row["favorite"]) if row else False


def get_categories(db_path: Optional[str | Path] = None) -> List[str]:
    """Returns all unique category names present in the library."""
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT DISTINCT category FROM library ORDER BY category ASC")
    categories = [row["category"] for row in cursor.fetchall() if row["category"]]
    conn.close()
    return categories
