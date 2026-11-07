"""Command execution logging and history queries for Command Center."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from command_center.db import get_connection

PREVIEW_MAX_BYTES = 2048
MAX_HISTORY_ENTRIES = 10000


def log_command(
    command: str,
    shell: str,
    cwd: str,
    exit_code: int,
    duration_ms: int,
    output_preview: str = "",
    db_path: Optional[str | Path] = None,
) -> int:
    """
    Logs an executed command to SQLite history and updates matching library use_count.

    Returns:
        The inserted history row ID.
    """
    ran_at = datetime.now(timezone.utc).isoformat()
    # Ensure preview is limited to roughly 2 KB
    preview_truncated = output_preview[:PREVIEW_MAX_BYTES] if output_preview else ""

    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO history (command, shell, cwd, ran_at, exit_code, duration_ms, output_preview)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                command,
                shell.lower(),
                cwd,
                ran_at,
                exit_code,
                duration_ms,
                preview_truncated,
            ),
        )
        history_id = cursor.lastrowid or 0

        # Increment use_count and set last_used_at for matching library items
        conn.execute(
            """
            UPDATE library
            SET use_count = use_count + 1,
                last_used_at = ?
            WHERE command = ? AND (shell = ? OR shell = 'both')
            """,
            (ran_at, command, shell.lower()),
        )

        # Prune old history entries beyond cap
        conn.execute(
            """
            DELETE FROM history
            WHERE id NOT IN (
                SELECT id FROM history ORDER BY id DESC LIMIT ?
            )
            """,
            (MAX_HISTORY_ENTRIES,),
        )

    conn.close()
    return history_id


def get_history(
    search: str = "",
    shell: Optional[str] = None,
    failed_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieves filtered command history rows ordered by most recent first."""
    conn = get_connection(db_path)
    query = "SELECT id, command, shell, cwd, ran_at, exit_code, duration_ms, output_preview FROM history WHERE 1=1"
    params: List[Any] = []

    if search.strip():
        query += " AND command LIKE ?"
        params.append(f"%{search.strip()}%")

    if shell and shell.lower() in ("cmd", "powershell"):
        query += " AND shell = ?"
        params.append(shell.lower())

    if failed_only:
        query += " AND exit_code != 0"

    query += " ORDER BY ran_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_most_used(
    limit: int = 25,
    shell: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> List[Dict[str, Any]]:
    """Retrieves top commands by execution frequency."""
    conn = get_connection(db_path)
    query = """
        SELECT command, shell, COUNT(*) as count, MAX(ran_at) as last_ran,
               SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) as successes,
               AVG(duration_ms) as avg_duration_ms
        FROM history
        WHERE 1=1
    """
    params: List[Any] = []

    if shell and shell.lower() in ("cmd", "powershell"):
        query += " AND shell = ?"
        params.append(shell.lower())

    query += " GROUP BY command, shell ORDER BY count DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_recent_unique_commands(
    limit: int = 50,
    shell: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> List[str]:
    """Returns recent distinct command strings (useful for Up/Down input cycling)."""
    conn = get_connection(db_path)
    query = """
        SELECT command FROM (
            SELECT command, MAX(id) as max_id
            FROM history
            WHERE 1=1
    """
    params: List[Any] = []
    if shell and shell.lower() in ("cmd", "powershell"):
        query += " AND shell = ?"
        params.append(shell.lower())

    query += """
            GROUP BY command
            ORDER BY max_id DESC
            LIMIT ?
        )
        ORDER BY max_id ASC
    """
    params.append(limit)

    cursor = conn.execute(query, params)
    commands = [row["command"] for row in cursor.fetchall()]
    conn.close()
    return commands
