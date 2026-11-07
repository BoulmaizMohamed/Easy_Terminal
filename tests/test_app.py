"""UI and Integration tests for Command Center."""

import asyncio
from command_center.app import CommandCenterApp


def test_app_command_execution():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            inp = app.query_one("#command-input")
            inp.value = "Write-Output 'Textual Test'"
            await pilot.press("enter")
            await pilot.pause(1.0)

            log = app.query_one("#output-log")
            rendered_text = "\n".join(line.text for line in log.lines)

            assert "Textual Test" in rendered_text
            assert "exit: 0" in rendered_text

            # Test theme toggle action
            initial_theme = app.theme
            app.action_toggle_theme()
            assert app.theme != initial_theme

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_history_screen_flow():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Run a command to ensure history exists
            inp = app.query_one("#command-input")
            inp.value = "Write-Output 'HistoryEntry123'"
            await pilot.press("enter")
            await pilot.pause(1.0)

            # Open history screen
            await pilot.press("ctrl+h")
            await pilot.pause(0.5)

            # Verify history screen is active
            from command_center.history_screen import HistoryScreen
            assert isinstance(app.screen, HistoryScreen)

            table = app.screen.query_one("#history-table")
            assert table.row_count > 0

            # Press Escape to close history screen
            await pilot.press("escape")
            await pilot.pause(0.5)

            # We should be back on the main screen
            assert not isinstance(app.screen, HistoryScreen)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_f2_shell_toggle():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            assert app.shell.shell_type == "powershell"

            # Press F2 to toggle to cmd
            await pilot.press("f2")
            await pilot.pause(0.5)

            assert app.shell.shell_type == "cmd"
            status_shell = app.query_one("#status-shell")
            assert "CMD" in str(status_shell.content)

            # Execute a CMD command
            inp = app.query_one("#command-input")
            inp.value = "echo hello_from_cmd_test"
            await pilot.press("enter")
            await pilot.pause(1.0)

            log = app.query_one("#output-log")
            rendered_text = "\n".join(line.text for line in log.lines)
            assert "hello_from_cmd_test" in rendered_text

            # Press F2 to toggle back to PowerShell
            await pilot.press("f2")
            await pilot.pause(0.5)
            assert app.shell.shell_type == "powershell"

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_auto_suggest_flow():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # 1. Execute a command to seed history
            inp = app.query_one("#command-input")
            inp.value = "Get-UniqueProcessXYZ"
            await pilot.press("enter")
            await pilot.pause(1.0)

            # 2. Type partial prefix
            inp.value = "Get-Unique"
            await pilot.pause(0.5)

            sugg_box = app.query_one("#suggestions-container")
            assert sugg_box.has_class("visible")

            sugg_list = app.query_one("#suggestions-list")
            assert sugg_list.option_count > 0

            # 3. Press Tab to accept suggestion
            await pilot.press("tab")
            await pilot.pause(0.2)

            assert inp.value == "Get-UniqueProcessXYZ"
            assert not sugg_box.has_class("visible")

            # 4. Type partial prefix again and press Escape to close
            inp.value = "Get-Un"
            await pilot.pause(0.5)
            assert sugg_box.has_class("visible")

            await pilot.press("escape")
            await pilot.pause(0.2)
            assert not sugg_box.has_class("visible")

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_library_screen_flow():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Open Library via Ctrl+L
            await pilot.press("ctrl+l")
            await pilot.pause(0.5)

            from command_center.library_screen import LibraryScreen
            assert isinstance(app.screen, LibraryScreen)

            table = app.screen.query_one("#library-table")
            assert table.row_count >= 40

            # Press escape to close
            await pilot.press("escape")
            await pilot.pause(0.5)
            assert not isinstance(app.screen, LibraryScreen)

        app.shell_manager.close_all()

    asyncio.run(_test())


def test_merged_library_suggestions():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            inp = app.query_one("#command-input")
            # Type 'robocopy' which is in seed library
            inp.value = "robocopy"
            await pilot.pause(0.5)

            sugg_box = app.query_one("#suggestions-container")
            assert sugg_box.has_class("visible")

            sugg_list = app.query_one("#suggestions-list")
            assert sugg_list.option_count > 0

            # First suggestion should be robocopy with description
            first_opt = sugg_list.get_option_at_index(0)
            assert "robocopy" in str(first_opt.prompt).lower()

        app.shell_manager.close_all()

    asyncio.run(_test())
