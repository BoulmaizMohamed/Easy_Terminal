"""JSON Import and Export for Command Center library entries."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from command_center.db import get_connection


def export_library_json(
    output_path: str | Path,
    user_only: bool = True,
    db_path: Optional[str | Path] = None,
) -> int:
    """
    Exports library entries to a JSON file.

    Args:
        output_path: File destination.
        user_only: If True, only exports source='user' entries.
        db_path: Optional SQLite database path.

    Returns:
        The count of exported entries.
    """
    conn = get_connection(db_path)
    if user_only:
        cursor = conn.execute(
            """
            SELECT name, command, shell, category, description, example, tags, favorite, use_count, source
            FROM library
            WHERE source = 'user'
            ORDER BY category ASC, name ASC
            """
        )
    else:
        cursor = conn.execute(
            """
            SELECT name, command, shell, category, description, example, tags, favorite, use_count, source
            FROM library
            ORDER BY category ASC, name ASC
            """
        )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    return len(rows)


def import_library_json(
    input_path: str | Path,
    db_path: Optional[str | Path] = None,
) -> Tuple[int, int]:
    """
    Imports command entries from a JSON file.
    Validates schema and skips duplicates on (command, shell, source).

    Returns:
        Tuple of (added_count, skipped_count).
    """
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Import file does not exist: {src}")

    with open(src, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file format: {e}")

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of command objects.")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    added = 0
    skipped = 0

    with conn:
        for item in data:
            if not isinstance(item, dict):
                skipped += 1
                continue

            name = item.get("name")
            command = item.get("command")
            if not name or not command or not str(name).strip() or not str(command).strip():
                skipped += 1
                continue

            shell = str(item.get("shell", "both")).lower()
            if shell not in ("cmd", "powershell", "both"):
                shell = "both"

            category = str(item.get("category", "General")).strip() or "General"
            description = str(item.get("description", "")).strip()
            example = str(item.get("example", "")).strip()
            tags = str(item.get("tags", "")).strip()
            favorite = 1 if item.get("favorite") else 0
            source = str(item.get("source", "user")).strip() or "user"

            cursor = conn.execute(
                """
                INSERT INTO library (name, command, shell, category, description, example, tags, favorite, use_count, source, date_added, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                ON CONFLICT(command, shell, source) DO NOTHING
                """,
                (
                    name.strip(),
                    command.strip(),
                    shell,
                    category,
                    description,
                    example,
                    tags,
                    favorite,
                    source,
                    now,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                added += 1
            else:
                skipped += 1

    conn.close()
    return added, skipped
