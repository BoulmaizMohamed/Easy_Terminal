"""Unit tests for Command Palette and Help dialog."""

import asyncio
import pytest
from command_center.app import CommandCenterApp
from command_center.db import init_db
from command_center.library import load_seed_library
from command_center.palette_screen import PaletteScreen


def test_palette_screen_search_and_actions():
    async def _test():
        app = CommandCenterApp()
        async with app.run_test() as pilot:
            # Open Palette via Ctrl+P
            await pilot.press("ctrl+p")
            await pilot.pause(0.5)

            assert isinstance(app.screen, PaletteScreen)
            palette = app.screen

            # Search for a seed command
            search_input = palette.query_one("#palette-search")
            search_input.value = "ping"
            await pilot.pause(0.5)

            assert len(palette.entries) > 0
            assert any("ping" in e["command"].lower() for e in palette.entries)

            # Test Insert into input via Tab
            await pilot.press("tab")
            await pilot.pause(0.5)

            # Should be back on main screen with command inserted
            assert not isinstance(app.screen, PaletteScreen)
            main_input = app.query_one("#command-input")
            assert "ping" in main_input.value.lower()

        app.shell_manager.close_all()

    asyncio.run(_test())
