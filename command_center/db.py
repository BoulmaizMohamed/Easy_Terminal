"""Database setup, schema, and connection management for Command Center."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

import platformdirs

DEFAULT_DB_DIR = Path(platformdirs.user_data_dir("command_center", appauthor=False, roaming=True))
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "command_center.db"


def get_db_path(custom_path: Optional[str | Path] = None) -> Path:
    """Returns the resolved SQLite database path."""
    if custom_path:
        path = Path(custom_path)
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """Creates a new SQLite connection with foreign keys and Row factory enabled."""
    resolved_path = get_db_path(db_path)
    conn = sqlite3.connect(resolved_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[str | Path] = None) -> None:
    """Initializes tables and indexes as defined in the data model."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                shell TEXT NOT NULL CHECK (shell IN ('cmd','powershell')),
                cwd TEXT,
                ran_at TEXT NOT NULL,          -- ISO 8601 UTC
                exit_code INTEGER,
                duration_ms INTEGER,
                output_preview TEXT            -- first ~2 KB only
            );
            CREATE INDEX IF NOT EXISTS idx_history_command ON history(command);
            CREATE INDEX IF NOT EXISTS idx_history_ran_at ON history(ran_at);

            CREATE TABLE IF NOT EXISTS library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                shell TEXT NOT NULL CHECK (shell IN ('cmd','powershell','both')),
                category TEXT NOT NULL DEFAULT 'General',
                description TEXT,
                example TEXT,
                tags TEXT,
                favorite INTEGER NOT NULL DEFAULT 0,
                use_count INTEGER NOT NULL DEFAULT 0,
                last_used_at TEXT,
                source TEXT NOT NULL DEFAULT 'user',
                date_added TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (command, shell, source)
            );
            """
        )
    conn.close()
