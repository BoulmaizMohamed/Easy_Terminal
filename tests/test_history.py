"""Unit tests for SQLite database and history logging."""

import os
import sqlite3
import pytest
from command_center.db import get_connection, init_db
from command_center.history import (
    get_history,
    get_most_used,
    get_recent_unique_commands,
    log_command,
)


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh temporary database path for each test."""
    db_file = tmp_path / "test_cmd_center.db"
    init_db(db_file)
    return db_file


def test_init_db(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    )
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()

    assert "history" in tables
    assert "library" in tables


def test_log_command_and_query(temp_db):
    long_output = "A" * 5000
    hid = log_command(
        command="Get-Service",
        shell="powershell",
        cwd="C:\\Test",
        exit_code=0,
        duration_ms=120,
        output_preview=long_output,
        db_path=temp_db,
    )
    assert hid > 0

    entries = get_history(db_path=temp_db)
    assert len(entries) == 1
    item = entries[0]
    assert item["command"] == "Get-Service"
    assert item["shell"] == "powershell"
    assert item["exit_code"] == 0
    assert len(item["output_preview"]) <= 2048


def test_history_search_and_filter(temp_db):
    log_command("dir", "cmd", "C:\\", 0, 10, db_path=temp_db)
    log_command("Get-Process", "powershell", "C:\\", 0, 50, db_path=temp_db)
    log_command("Get-Item Invalid", "powershell", "C:\\", 1, 30, db_path=temp_db)

    # Search filter
    assert len(get_history(search="Get-", db_path=temp_db)) == 2
    assert len(get_history(search="dir", db_path=temp_db)) == 1

    # Shell filter
    assert len(get_history(shell="cmd", db_path=temp_db)) == 1
    assert len(get_history(shell="powershell", db_path=temp_db)) == 2

    # Failed only
    failed = get_history(failed_only=True, db_path=temp_db)
    assert len(failed) == 1
    assert failed[0]["command"] == "Get-Item Invalid"


def test_most_used_commands(temp_db):
    for _ in range(3):
        log_command("git status", "powershell", "C:\\", 0, 15, db_path=temp_db)
    for _ in range(5):
        log_command("ls", "powershell", "C:\\", 0, 5, db_path=temp_db)

    top = get_most_used(limit=5, db_path=temp_db)
    assert len(top) == 2
    assert top[0]["command"] == "ls"
    assert top[0]["count"] == 5
    assert top[1]["command"] == "git status"
    assert top[1]["count"] == 3


def test_recent_unique_commands(temp_db):
    log_command("cmd1", "powershell", "C:\\", 0, 1, db_path=temp_db)
    log_command("cmd2", "powershell", "C:\\", 0, 1, db_path=temp_db)
    log_command("cmd1", "powershell", "C:\\", 0, 1, db_path=temp_db)

    recent = get_recent_unique_commands(db_path=temp_db)
    assert recent == ["cmd2", "cmd1"]


def test_recent_unique_commands_selects_newest_under_limit(temp_db):
    for i in range(1, 61):
        log_command(f"cmd_{i}", "powershell", "C:\\", 0, 1, db_path=temp_db)
    recent = get_recent_unique_commands(limit=10, db_path=temp_db)
    assert recent == [f"cmd_{i}" for i in range(51, 61)]


def test_library_use_count_increment(temp_db):
    conn = get_connection(temp_db)
    with conn:
        conn.execute(
            """
            INSERT INTO library (name, command, shell, category, date_added, updated_at)
            VALUES ('Process list', 'Get-Process', 'powershell', 'System', '2026-01-01', '2026-01-01')
            """
        )
    conn.close()

    log_command("Get-Process", "powershell", "C:\\", 0, 20, db_path=temp_db)

    conn = get_connection(temp_db)
    row = conn.execute("SELECT use_count, last_used_at FROM library WHERE command = 'Get-Process'").fetchone()
    conn.close()

    assert row["use_count"] == 1
    assert row["last_used_at"] is not None
