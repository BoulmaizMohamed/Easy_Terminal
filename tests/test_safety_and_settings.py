"""Unit tests for dangerous command detection and user settings."""

import asyncio
from command_center.app import CommandCenterApp
from command_center.safety import is_dangerous_command
from command_center.safety_dialog import SafetyConfirmationDialog
from command_center.settings import AppSettings, load_settings, save_settings
from command_center.settings_screen import SettingsScreen


def test_dangerous_command_detection():
    # Dangerous commands
    assert is_dangerous_command("del /s *.*")[0] is True
    assert is_dangerous_command("del/s *.*")[0] is True
    assert is_dangerous_command("del /s /q C:\\temp")[0] is True
    assert is_dangerous_command("rd/s C:\\temp")[0] is True
    assert is_dangerous_command("rd /s /q C:\\temp")[0] is True
    assert is_dangerous_command("rmdir /s mydir")[0] is True
    assert is_dangerous_command("format C:")[0] is True
    assert is_dangerous_command("Remove-Item -Recurse C:\\dir")[0] is True
    assert is_dangerous_command("Remove-Item -Recurse -Force C:\\dir")[0] is True
    assert is_dangerous_command("rm -rf /")[0] is True
    assert is_dangerous_command("diskpart")[0] is True
    assert is_dangerous_command("shutdown /s /t 0")[0] is True
    assert is_dangerous_command("reg delete HKLM\\Software\\Test")[0] is True

    # Safe commands
    assert is_dangerous_command("dir")[0] is False
    assert is_dangerous_command("Get-Process")[0] is False
    assert is_dangerous_command("Get-Process | Format-Table")[0] is False
    assert is_dangerous_command("Get-Service | format-list")[0] is False
    assert is_dangerous_command("echo del")[0] is False
    assert is_dangerous_command("git status")[0] is False


def test_settings_load_and_save(tmp_path):
    settings_file = tmp_path / "settings.json"
    defaults = load_settings(settings_file)
    assert defaults.theme == "catppuccin-mocha"
    assert defaults.default_shell == "powershell"
    assert defaults.safety_enabled is True

    # Modify and save
    custom = AppSettings(
        theme="nord",
        default_shell="cmd",
        library_enter_action="insert",
        history_retention="off",
        safety_enabled=False,
    )
    save_settings(custom, settings_file)

    loaded = load_settings(settings_file)
    assert loaded.theme == "nord"
    assert loaded.default_shell == "cmd"
    assert loaded.library_enter_action == "insert"
    assert loaded.history_retention == "off"
    assert loaded.safety_enabled is False


def test_safety_dialog_intercept_and_cancel():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            inp = app.query_one("#command-input")
            # Try running a flagged command
            inp.value = "del /s test_file.tmp"
            await pilot.press("enter")
            await pilot.pause(0.5)

            # SafetyConfirmationDialog must be active
            assert isinstance(app.screen, SafetyConfirmationDialog)

            # Cancel via Escape
            await pilot.press("escape")
            await pilot.pause(0.5)

            assert not isinstance(app.screen, SafetyConfirmationDialog)
            # Verify command was cancelled in log
            log = app.query_one("#output-log")
            rendered = "\n".join(l.text for l in log.lines)
            assert "Cancelled" in rendered or "cancelled" in rendered

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_settings_screen_flow():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Open Settings via F10
            await pilot.press("f10")
            await pilot.pause(0.5)

            assert isinstance(app.screen, SettingsScreen)

            # Cycle theme button
            await pilot.click("#btn-theme-cycle")
            await pilot.pause(0.2)

            # Save preferences via Enter
            await pilot.press("enter")
            await pilot.pause(0.5)

            assert not isinstance(app.screen, SettingsScreen)

        app.shell_manager.close_all()

    asyncio.run(_test())
