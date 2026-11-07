"""Unit tests for tldr importer and JSON import/export."""

import io
import json
import zipfile
import pytest
from command_center.db import get_connection, init_db
from command_center.importers.json_sync import export_library_json, import_library_json
from command_center.importers.tldr import map_category, parse_tldr_content, sync_tldr_pages
from command_center.library import add_library_entry, get_library_entries


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_importers.db"
    init_db(db_file)
    return db_file


def test_parse_tldr_content():
    sample_page = """# ping

> Send ICMP ECHO_REQUEST to network hosts.
> More information: <https://learn.microsoft.com/windows-server/administration/windows-commands/ping>.

- Ping a remote host:

`ping {{host}}`

- Ping a host a specific number of times:

`ping -n {{count}} {{host}}`
"""
    entries = parse_tldr_content(sample_page, platform="windows")
    assert len(entries) == 2

    assert entries[0]["name"] == "ping: Ping a remote host"
    assert entries[0]["command"] == "ping {{host}}"
    assert entries[0]["shell"] == "cmd"
    assert entries[0]["category"] == "Network"
    assert "ICMP ECHO_REQUEST" in entries[0]["description"]

    assert entries[1]["name"] == "ping: Ping a host a specific number of times"
    assert entries[1]["command"] == "ping -n {{count}} {{host}}"


def test_map_category():
    assert map_category("robocopy", "Robust copy", "robocopy src dest") == "Files"
    assert map_category("netstat", "Network connections", "netstat -ano") == "Network"
    assert map_category("taskkill", "Terminate process", "taskkill /f /im test.exe") == "Processes"
    assert map_category("chkdsk", "Check disk", "chkdsk C:") == "Disk"
    assert map_category("whoami", "Display user", "whoami") == "Users"
    assert map_category("unknown", "something else", "foo bar") == "General"


def test_sync_tldr_with_mock_zip(temp_db):
    # Create mock tldr zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "pages/windows/testcmd.md",
            "# testcmd\n> A windows test tool.\n\n- Run test:\n`testcmd /run`\n",
        )
        zf.writestr(
            "pages/common/commontool.md",
            "# commontool\n> A common utility.\n\n- Execute tool:\n`commontool --all`\n",
        )
    mock_zip_bytes = buf.getvalue()

    # Pre-insert user command that matches command text to verify user protection
    add_library_entry(
        name="User Custom Tool",
        command="commontool --all",
        shell="both",
        category="Custom",
        source="user",
        db_path=temp_db,
    )

    added, updated = sync_tldr_pages(db_path=temp_db, custom_zip_data=mock_zip_bytes)
    assert added >= 1

    entries = get_library_entries(db_path=temp_db)
    # The user entry should remain source='user' and name='User Custom Tool'
    user_entry = [e for e in entries if e["command"] == "commontool --all" and e["source"] == "user"]
    assert len(user_entry) == 1
    assert user_entry[0]["name"] == "User Custom Tool"


def test_json_export_and_import(temp_db, tmp_path):
    # Add two user commands
    add_library_entry("Backup Script", "python backup.py", "both", "Custom", db_path=temp_db)
    add_library_entry("Lint Code", "flake8 .", "both", "Code", db_path=temp_db)

    export_file = tmp_path / "export.json"
    exported_count = export_library_json(export_file, user_only=True, db_path=temp_db)
    assert exported_count == 2
    assert export_file.exists()

    # Import into fresh DB
    new_db = tmp_path / "fresh.db"
    init_db(new_db)

    added, skipped = import_library_json(export_file, db_path=new_db)
    assert added == 2
    assert skipped == 0

    # Re-importing should skip duplicates
    added_second, skipped_second = import_library_json(export_file, db_path=new_db)
    assert added_second == 0
    assert skipped_second == 2

    imported_entries = get_library_entries(db_path=new_db)
    assert len(imported_entries) == 2
    names = {e["name"] for e in imported_entries}
    assert "Backup Script" in names
    assert "Lint Code" in names


def test_json_import_validation(temp_db, tmp_path):
    bad_file = tmp_path / "bad.json"
    with open(bad_file, "w") as f:
        json.dump([{"invalid": "no name or command"}, {"name": "Valid", "command": "echo 1"}], f)

    added, skipped = import_library_json(bad_file, db_path=temp_db)
    assert added == 1
    assert skipped == 1
