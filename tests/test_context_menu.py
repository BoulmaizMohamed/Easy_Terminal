"""Tests for Windows Explorer Context Menu integration and initial_cwd launching."""

import asyncio
from pathlib import Path

from command_center.app import CommandCenterApp
from command_center.context_menu import (
    is_context_menu_registered,
    register_context_menu,
    unregister_context_menu,
)


def test_context_menu_registration_and_cleanup(tmp_path):
    dummy_exe = tmp_path / "Easy_Terminal.exe"
    dummy_exe.write_text("dummy", encoding="utf-8")

    # 1. Clean state
    unregister_context_menu()
    assert not is_context_menu_registered()

    # 2. Register
    success = register_context_menu(exe_path=str(dummy_exe), title="Open in Terminal")
    assert success is True
    assert is_context_menu_registered() is True

    # 3. Verify registry entries via winreg
    import winreg
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Classes\Directory\Background\shell\EasyTerminal",
    ) as key:
        val, _ = winreg.QueryValueEx(key, "")
        assert val == "Open in Terminal"
        icon, _ = winreg.QueryValueEx(key, "Icon")
        assert str(dummy_exe) in icon

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Classes\Directory\Background\shell\EasyTerminal\command",
    ) as cmd_key:
        cmd_val, _ = winreg.QueryValueEx(cmd_key, "")
        assert str(dummy_exe) in cmd_val
        assert '"%V"' in cmd_val

    # 4. Unregister
    clean_success = unregister_context_menu()
    assert clean_success is True
    assert not is_context_menu_registered()


def test_app_launched_with_initial_cwd(tmp_path):
    async def _test():
        folder = tmp_path / "right-clicked-folder"
        folder.mkdir()

        app = CommandCenterApp(initial_cwd=str(folder))
        async with app.run_test() as pilot:
            await pilot.pause(0.5)

            # Working directory should match folder
            assert Path(app.shell.cwd).resolve() == folder.resolve()

            # Status bar should display folder
            status_cwd = app.query_one("#status-cwd")
            assert str(folder.resolve()) in str(status_cwd.content)

        app.shell_manager.close_all()

    asyncio.run(_test())
