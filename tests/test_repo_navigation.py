"""Tests for Repository Navigation via Command and UI (Ctrl+G, 'repo' command, and Quick Action)."""

import asyncio
import os
from pathlib import Path

from command_center.app import CommandCenterApp
from command_center.git_info import (
    find_repository,
    get_known_repositories,
    get_location_info,
    record_repository,
)
from command_center.repo_screen import RepoScreen


def test_repo_db_record_and_search(tmp_path):
    db_file = tmp_path / "test_repos.db"
    from command_center.db import init_db
    init_db(db_file)

    # Create dummy repos
    repo1 = tmp_path / "backend-api"
    repo1.mkdir()
    (repo1 / ".git").mkdir()
    (repo1 / ".git" / "HEAD").write_text("ref: refs/heads/develop\n", encoding="utf-8")

    repo2 = tmp_path / "frontend-web"
    repo2.mkdir()
    (repo2 / ".git").mkdir()
    (repo2 / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    # Record repo
    record_repository(str(repo1), "backend-api", "develop", db_path=db_file)
    record_repository(str(repo2), "frontend-web", "main", db_path=db_file)

    known = get_known_repositories(db_path=db_file, scan_neighbors=False)
    names = [r["name"] for r in known]
    assert "backend-api" in names
    assert "frontend-web" in names

    # Test find_repository
    match_exact = find_repository("backend-api", db_path=db_file)
    assert match_exact is not None
    assert match_exact["name"] == "backend-api"

    match_prefix = find_repository("front", db_path=db_file)
    assert match_prefix is not None
    assert match_prefix["name"] == "frontend-web"

    match_substr = find_repository("end-api", db_path=db_file)
    assert match_substr is not None
    assert match_substr["name"] == "backend-api"

    # Direct directory path lookup
    match_path = find_repository(str(repo2), db_path=db_file)
    assert match_path is not None
    assert match_path["name"] == "frontend-web"


def test_command_repo_list_and_navigation(tmp_path):
    async def _test():
        # Setup dummy target repo
        target_repo = tmp_path / "sample-project"
        target_repo.mkdir()
        (target_repo / ".git").mkdir()
        (target_repo / ".git" / "HEAD").write_text("ref: refs/heads/master\n", encoding="utf-8")

        record_repository(str(target_repo), "sample-project", "master")

        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # 1. Test "repo list" output
            inp = app.query_one("#command-input")
            inp.value = "repo list"
            await pilot.press("enter")
            await pilot.pause(0.5)

            log = app.query_one("#output-log")
            rendered = "\n".join(line.text for line in log.lines)
            assert "Known Git Repositories" in rendered
            assert "sample-project" in rendered

            # 2. Test "repo <name>" command navigation
            inp.value = "repo sample-project"
            await pilot.press("enter")
            await pilot.pause(1.0)

            # Active shell should have navigated to sample-project
            assert Path(app.shell.cwd).resolve() == target_repo.resolve()

            # Status bar and prompt symbol must reflect the new repo
            status_cwd = app.query_one("#status-cwd")
            assert str(target_repo.resolve()) in str(status_cwd.content)

            status_repo = app.query_one("#status-repo")
            assert "sample-project" in str(status_repo.content)

            prompt_sym = app.query_one("#prompt-symbol")
            assert "sample-project" in str(prompt_sym.content)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_ui_repo_navigator_screen_flow(tmp_path):
    async def _test():
        target_repo = tmp_path / "nav-ui-project"
        target_repo.mkdir()
        (target_repo / ".git").mkdir()
        (target_repo / ".git" / "HEAD").write_text("ref: refs/heads/v2-release\n", encoding="utf-8")

        record_repository(str(target_repo), "nav-ui-project", "v2-release")

        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # 1. Click Quick Action button '#qa-repos'
            qa_btn = app.query_one("#qa-repos")
            qa_btn.press()
            await pilot.pause(0.5)

            # RepoScreen modal should now be active
            assert isinstance(app.screen, RepoScreen)

            # Filter input by repo name
            search_input = app.screen.query_one("#repo-search")
            search_input.value = "nav-ui"
            await pilot.pause(0.3)

            # Press Enter to select and navigate
            await pilot.press("enter")
            await pilot.pause(1.0)

            # Modal dismissed, back to main screen
            assert not isinstance(app.screen, RepoScreen)

            # App shell has navigated
            assert Path(app.shell.cwd).resolve() == target_repo.resolve()

            # 2. Press Ctrl+G keyboard shortcut to open navigator again
            await pilot.press("ctrl+g")
            await pilot.pause(0.5)
            assert isinstance(app.screen, RepoScreen)

            # Press Escape to close without selecting
            await pilot.press("escape")
            await pilot.pause(0.3)
            assert not isinstance(app.screen, RepoScreen)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_repo_screen_arrow_keys_and_action_buttons(tmp_path):
    async def _test():
        repo_a = tmp_path / "repo-alpha"
        repo_a.mkdir()
        (repo_a / ".git").mkdir()
        (repo_a / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

        repo_b = tmp_path / "repo-beta"
        repo_b.mkdir()
        (repo_b / ".git").mkdir()
        (repo_b / ".git" / "HEAD").write_text("ref: refs/heads/dev\n", encoding="utf-8")

        record_repository(str(repo_a), "repo-alpha", "main")
        record_repository(str(repo_b), "repo-beta", "dev")

        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Open repos modal
            await pilot.press("ctrl+g")
            await pilot.pause(0.5)
            assert isinstance(app.screen, RepoScreen)

            repo_list = app.screen.query_one("#repo-list")
            assert repo_list.option_count >= 2
            initial_idx = repo_list.highlighted
            assert initial_idx == 0

            # Press down arrow from search input to verify on_key interception
            await pilot.press("down")
            await pilot.pause(0.2)
            assert repo_list.highlighted == 1

            # Press up arrow
            await pilot.press("up")
            await pilot.pause(0.2)
            assert repo_list.highlighted == 0

            # Press down again to highlight repo-beta
            await pilot.press("down")
            await pilot.pause(0.2)

            # Click the Action Button 'Navigate'
            btn_nav = app.screen.query_one("#btn-repo-navigate")
            btn_nav.press()
            await pilot.pause(1.0)

            # Should have navigated and closed modal
            assert not isinstance(app.screen, RepoScreen)

            # Re-open and test 'Cancel' button
            await pilot.press("ctrl+g")
            await pilot.pause(0.5)
            assert isinstance(app.screen, RepoScreen)

            btn_cancel = app.screen.query_one("#btn-repo-cancel")
            btn_cancel.press()
            await pilot.pause(0.3)
            assert not isinstance(app.screen, RepoScreen)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_command_cd_repo_fallback(tmp_path):
    async def _test():
        remote_repo = tmp_path / "distant-repo"
        remote_repo.mkdir()
        (remote_repo / ".git").mkdir()
        (remote_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

        record_repository(str(remote_repo), "distant-repo", "main")

        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Execute "cd distant-repo"
            inp = app.query_one("#command-input")
            inp.value = "cd distant-repo"
            await pilot.press("enter")
            await pilot.pause(1.0)

            # Should have smartly navigated to remote_repo
            assert Path(app.shell.cwd).resolve() == remote_repo.resolve()
            status_cwd = app.query_one("#status-cwd")
            assert str(remote_repo.resolve()) in str(status_cwd.content)

        app.shell_manager.close_all()

    asyncio.run(_test())
