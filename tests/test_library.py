"""Unit tests for Command Center library CRUD, sorting, and seed loading."""

import pytest
from command_center.db import get_connection, init_db
from command_center.library import (
    add_library_entry,
    delete_library_entry,
    get_categories,
    get_library_entries,
    load_seed_library,
    toggle_favorite,
    update_library_entry,
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_library.db"
    init_db(db_file)
    return db_file


def test_seed_library_loading(temp_db):
    inserted = load_seed_library(db_path=temp_db)
    assert inserted >= 45

    # Second load should insert 0 duplicates
    assert load_seed_library(db_path=temp_db) == 0

    entries = get_library_entries(db_path=temp_db)
    assert len(entries) >= 45
    categories = get_categories(db_path=temp_db)
    assert "Network" in categories
    assert "Files" in categories


def test_library_crud_and_safety(temp_db):
    # Add user entry
    eid = add_library_entry(
        name="My Custom Ping",
        command="ping 127.0.0.1",
        shell="both",
        category="Network",
        description="Pings local interface",
        example="ping 127.0.0.1",
        tags="local,ping",
        favorite=True,
        db_path=temp_db,
    )
    assert eid > 0

    entries = get_library_entries(search="Custom Ping", db_path=temp_db)
    assert len(entries) == 1
    assert entries[0]["name"] == "My Custom Ping"
    assert entries[0]["favorite"] == 1

    # Toggle favorite
    new_fav = toggle_favorite(eid, db_path=temp_db)
    assert new_fav is False

    # Update entry
    ok = update_library_entry(
        eid,
        name="Updated Ping",
        command="ping -n 10 127.0.0.1",
        shell="cmd",
        category="Diagnostics",
        description="Updated desc",
        example="ping -n 10 127.0.0.1",
        tags="updated",
        favorite=True,
        db_path=temp_db,
    )
    assert ok is True

    # User entry delete
    assert delete_library_entry(eid, db_path=temp_db) is True
    assert len(get_library_entries(search="Updated Ping", db_path=temp_db)) == 0


def test_seed_entry_protection(temp_db):
    load_seed_library(db_path=temp_db)
    entries = get_library_entries(source="seed", db_path=temp_db)
    seed_id = entries[0]["id"]

    # Deleting seed entry without force should fail
    assert delete_library_entry(seed_id, force=False, db_path=temp_db) is False

    # Deleting with force works
    assert delete_library_entry(seed_id, force=True, db_path=temp_db) is True


def test_library_sorting_and_filters(temp_db):
    add_library_entry("Alpha", "cmd_alpha", "powershell", "Cat1", favorite=False, db_path=temp_db)
    add_library_entry("Beta", "cmd_beta", "powershell", "Cat2", favorite=True, db_path=temp_db)
    add_library_entry("Gamma", "cmd_gamma", "cmd", "Cat1", favorite=False, db_path=temp_db)

    # Sort alphabetical
    alpha = get_library_entries(sort_by="alphabetical", db_path=temp_db)
    names = [e["name"] for e in alpha]
    assert names == ["Alpha", "Beta", "Gamma"]

    # Sort favorites first
    favs = get_library_entries(sort_by="favorites_first", db_path=temp_db)
    assert favs[0]["name"] == "Beta"

    # Shell filter
    cmd_only = get_library_entries(shell="cmd", db_path=temp_db)
    assert len(cmd_only) == 1
    assert cmd_only[0]["name"] == "Gamma"

    # Category filter
    cat1_only = get_library_entries(category="Cat1", db_path=temp_db)
    assert len(cat1_only) == 2


def test_library_tier_filtering(temp_db):
    add_library_entry("Ping Local", "ping 127.0.0.1", "both", "Network", tags="ping,everyday", db_path=temp_db)
    add_library_entry("DISM Repair", "DISM /Online", "both", "System", tags="dism,repair,specialized", db_path=temp_db)

    everyday = get_library_entries(tier="everyday", db_path=temp_db)
    assert any(e["name"] == "Ping Local" for e in everyday)
    assert not any(e["name"] == "DISM Repair" for e in everyday)

    specialized = get_library_entries(tier="specialized", db_path=temp_db)
    assert any(e["name"] == "DISM Repair" for e in specialized)
    assert not any(e["name"] == "Ping Local" for e in specialized)
