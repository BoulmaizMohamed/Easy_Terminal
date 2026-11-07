"""Unit tests for auto-suggest ranking engine."""

import pytest
from command_center.db import get_connection, init_db
from command_center.history import log_command
from command_center.suggest import rank_suggestions


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_suggest.db"
    init_db(db_file)
    return db_file


def test_empty_query(temp_db):
    assert rank_suggestions("", "powershell", db_path=temp_db) == []
    assert rank_suggestions("   ", "powershell", db_path=temp_db) == []


def test_prefix_beats_substring(temp_db):
    # Prefix match
    log_command("git status", "powershell", "C:\\", 0, 10, db_path=temp_db)
    # Substring match
    log_command("do git pull", "powershell", "C:\\", 0, 10, db_path=temp_db)

    results = rank_suggestions("git", "powershell", db_path=temp_db)
    assert len(results) == 2
    assert results[0].command == "git status"
    assert results[1].command == "do git pull"


def test_frequency_ranking(temp_db):
    # Log 'git commit' once
    log_command("git commit", "powershell", "C:\\", 0, 10, db_path=temp_db)
    # Log 'git push' 5 times
    for _ in range(5):
        log_command("git push", "powershell", "C:\\", 0, 10, db_path=temp_db)

    results = rank_suggestions("git", "powershell", db_path=temp_db)
    commands = [r.command for r in results]
    assert commands.index("git push") < commands.index("git commit")


def test_shell_filtering(temp_db):
    log_command("dir /w", "cmd", "C:\\", 0, 10, db_path=temp_db)
    log_command("Get-ChildItem", "powershell", "C:\\", 0, 10, db_path=temp_db)

    ps_results = rank_suggestions("get", "powershell", db_path=temp_db)
    assert len(ps_results) == 1
    assert ps_results[0].command == "Get-ChildItem"

    cmd_results = rank_suggestions("dir", "cmd", db_path=temp_db)
    assert len(cmd_results) == 1
    assert cmd_results[0].command == "dir /w"


def test_library_favorite_boost(temp_db):
    conn = get_connection(temp_db)
    with conn:
        conn.execute(
            """
            INSERT INTO library (name, command, shell, category, favorite, date_added, updated_at)
            VALUES ('Git Log', 'git log --oneline', 'powershell', 'Git', 1, '2026-01-01', '2026-01-01')
            """
        )
    conn.close()

    log_command("git diff", "powershell", "C:\\", 0, 10, db_path=temp_db)

    results = rank_suggestions("git", "powershell", db_path=temp_db)
    assert len(results) >= 2
    # Favorite library command should be boosted to first place
    assert results[0].command == "git log --oneline"
    assert results[0].favorite is True


def test_limit_suggestions(temp_db):
    for i in range(15):
        log_command(f"test-cmd-{i:02d}", "powershell", "C:\\", 0, 10, db_path=temp_db)

    results = rank_suggestions("test", "powershell", db_path=temp_db, limit=8)
    assert len(results) == 8
