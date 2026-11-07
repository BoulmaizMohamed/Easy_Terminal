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
