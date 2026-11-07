"""Windows Explorer Context Menu Integration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import winreg
except ImportError:
    winreg = None  # Non-Windows fallback (e.g. CI)


def get_default_exe_path() -> str:
    """Returns absolute path to Easy_Terminal.exe, CommandCenter.exe or current Python executable."""
    if getattr(sys, "frozen", False):
        return sys.executable
    base = Path(__file__).resolve().parent.parent
    for candidate in [
        base / "dist" / "Easy_Terminal" / "Easy_Terminal.exe",
        base / "dist" / "CommandCenter" / "CommandCenter.exe",
    ]:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def register_context_menu(exe_path: Optional[str] = None, title: str = "Open in Terminal") -> bool:
    """Registers 'Open in Terminal' in Windows Explorer context menu for folders, backgrounds, and drives."""
    if not winreg:
        return False

    exe = str(Path(exe_path or get_default_exe_path()).resolve())
    targets = [
        (r"Software\Classes\Directory\Background\shell\EasyTerminal", f'"{exe}" "%V"'),
        (r"Software\Classes\Directory\shell\EasyTerminal", f'"{exe}" "%1"'),
        (r"Software\Classes\Drive\shell\EasyTerminal", f'"{exe}" "%1"'),
        (r"Software\Classes\Directory\Background\shell\CommandCenter", f'"{exe}" "%V"'),
        (r"Software\Classes\Directory\shell\CommandCenter", f'"{exe}" "%1"'),
        (r"Software\Classes\Drive\shell\CommandCenter", f'"{exe}" "%1"'),
    ]

    try:
        for subkey_path, cmd_str in targets:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, title)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{exe}"')
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{subkey_path}\command") as cmd_key:
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd_str)
        return True
    except Exception:
        return False


def unregister_context_menu() -> bool:
    """Removes 'Open in Terminal' entries from Windows Explorer context menu."""
    if not winreg:
        return False

    subkeys = [
        r"Software\Classes\Directory\Background\shell\EasyTerminal",
        r"Software\Classes\Directory\shell\EasyTerminal",
        r"Software\Classes\Drive\shell\EasyTerminal",
        r"Software\Classes\Directory\Background\shell\CommandCenter",
        r"Software\Classes\Directory\shell\CommandCenter",
        r"Software\Classes\Drive\shell\CommandCenter",
    ]

    success = True
    for subkey in subkeys:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, rf"{subkey}\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, subkey)
        except FileNotFoundError:
            pass
        except Exception:
            success = False
    return success


def is_context_menu_registered() -> bool:
    """Checks whether the context menu entry exists in the registry."""
    if not winreg:
        return False
    for subkey in (
        r"Software\Classes\Directory\Background\shell\EasyTerminal",
        r"Software\Classes\Directory\Background\shell\CommandCenter",
    ):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey):
                return True
        except FileNotFoundError:
            continue
        except Exception:
            pass
    return False
