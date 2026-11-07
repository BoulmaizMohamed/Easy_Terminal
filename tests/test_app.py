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

        app.shell.close()

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

        app.shell.close()

    asyncio.run(_test())
