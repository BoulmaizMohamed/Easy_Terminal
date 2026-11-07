"""Tests for Git repository & root indicator and French language support."""

import asyncio
import os
from pathlib import Path

from command_center.app import CommandCenterApp
from command_center.git_info import LocationInfo, get_location_info
from command_center.i18n import t
from command_center.settings import AppSettings, load_settings, save_settings
from command_center.settings_screen import SettingsScreen


def test_git_location_detection(tmp_path):
    # Test on a temporary non-git path
    non_git = tmp_path / "plain_dir"
    non_git.mkdir()
    info = get_location_info(str(non_git))
    assert info.is_git is False
    assert info.repo_name == ""
    assert "plain_dir" in info.get_prompt_badge()
    assert "Root" in info.get_repo_badge("en")
    assert "Racine" in info.get_repo_badge("fr")

    # Test on a simulated git repo
    git_dir = tmp_path / "my_project"
    git_dir.mkdir()
    dot_git = git_dir / ".git"
    dot_git.mkdir()
    (dot_git / "HEAD").write_text("ref: refs/heads/feature/awesome-ui\n", encoding="utf-8")

    git_info = get_location_info(str(git_dir))
    assert git_info.is_git is True
    assert git_info.repo_name == "my_project"
    assert git_info.branch == "feature/awesome-ui"
    assert "my_project" in git_info.get_prompt_badge()
    assert "(feature/awesome-ui)" in git_info.get_prompt_badge()
    assert "Repo: my_project [feature/awesome-ui]" in git_info.get_repo_badge("en")
    assert "Dépôt: my_project [feature/awesome-ui]" in git_info.get_repo_badge("fr")


def test_i18n_translation_and_fallback():
    # English translations
    assert t("qa_files", "en") == "📁 Files"
    assert t("status_ready", "en") == "Ready"

    # French translations
    assert t("qa_files", "fr") == "📁 Fichiers"
    assert t("status_ready", "fr") == "Prêt"
    assert t("qa_procs", "fr") == "⚡ Applications"
    assert t("qa_disks", "fr") == "💾 Disques"
    assert t("qa_library", "fr") == "📚 Bibliothèque"
    assert t("qa_clear", "fr") == "🧹 Effacer"

    # Fallback to English for unknown language
    assert t("qa_files", "es") == "📁 Files"

    # Fallback to key for unknown key
    assert t("non_existent_key_xyz", "fr") == "non_existent_key_xyz"


def test_settings_language_persistence(tmp_path):
    settings_file = tmp_path / "settings.json"
    s = AppSettings(language="fr")
    save_settings(s, settings_file)

    loaded = load_settings(settings_file)
    assert loaded.language == "fr"


def test_settings_screen_language_toggle():
    async def _test():
        initial_settings = AppSettings(language="en")
        screen = SettingsScreen(initial_settings)
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            await app.push_screen(screen)
            await pilot.pause(0.2)

            btn = screen.query_one("#btn-lang-toggle")
            assert "English" in str(btn.label)

            # Click to toggle language
            await pilot.click("#btn-lang-toggle")
            await pilot.pause(0.2)

            assert screen.settings.language == "fr"
            assert "Français" in str(btn.label)

            # Verify labels updated to French
            title = screen.query_one("#settings-title")
            assert "PARAMÈTRES" in str(title.content)

            # Close screen
            await pilot.press("escape")
            await pilot.pause(0.2)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_app_repo_indicator_and_language_switch():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.2)

            # Prompt symbol should contain repository or directory indicator
            prompt_sym = app.query_one("#prompt-symbol")
            assert "PS" in str(prompt_sym.content)
            assert "📁" in str(prompt_sym.content)

            # Status bar should display cwd, repo/root, exit code, and state
            status_repo = app.query_one("#status-repo")
            assert status_repo is not None

            # Switch language to French via settings callback
            new_settings = AppSettings(language="fr")
            app._on_settings_result(new_settings)
            await pilot.pause(0.2)

            assert app.settings.language == "fr"
            assert app.query_one("#qa-files").label == "📁 Fichiers"
            assert app.query_one("#qa-clear").label == "🧹 Effacer"
            assert str(app.query_one("#status-state").content) == "Prêt"

        app.shell_manager.close_all()

    asyncio.run(_test())
