"""User settings management for Command Center."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import platformdirs

DEFAULT_SETTINGS_DIR = Path(platformdirs.user_data_dir("command_center", appauthor=False, roaming=True))
DEFAULT_SETTINGS_FILE = DEFAULT_SETTINGS_DIR / "settings.json"


@dataclass
class AppSettings:
    """Command Center user settings."""

    theme: str = "catppuccin-mocha"
    default_shell: str = "powershell"
    library_enter_action: str = "run"  # "run" | "insert"
    history_retention: str = "preview"  # "preview" | "off"
    safety_enabled: bool = True


def load_settings(file_path: Optional[str | Path] = None) -> AppSettings:
    """Loads settings from disk or returns defaults if not present."""
    path = Path(file_path) if file_path else DEFAULT_SETTINGS_FILE
    if not path.exists():
        return AppSettings()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppSettings(
            theme=str(data.get("theme", "catppuccin-mocha")),
            default_shell=str(data.get("default_shell", "powershell")).lower(),
            library_enter_action=str(data.get("library_enter_action", "run")).lower(),
            history_retention=str(data.get("history_retention", "preview")).lower(),
            safety_enabled=bool(data.get("safety_enabled", True)),
        )
    except Exception:
        return AppSettings()


def save_settings(settings: AppSettings, file_path: Optional[str | Path] = None) -> None:
    """Saves user settings to disk as JSON."""
    path = Path(file_path) if file_path else DEFAULT_SETTINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, indent=2)
