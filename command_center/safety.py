"""Dangerous command pattern detection for Command Center safety."""

from __future__ import annotations

import re
from typing import List, Tuple

DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (
        r"(?i)\bdel\b\s+.*(/s|/q)",
        "Recursive or quiet file deletion (del /s /q)",
    ),
    (
        r"(?i)\b(rd|rmdir)\b\s+.*(/s|/q)",
        "Recursive directory removal (rd /s)",
    ),
    (
        r"(?i)\bformat(\s+[a-z]:)?\b",
        "Disk volume formatting (format)",
    ),
    (
        r"(?i)\b(remove-item|ri|rm)\b\s+.*(-recurse\s+-force|-force\s+-recurse|-r\s+-f|-rf)\b",
        "Forced recursive deletion (Remove-Item -Recurse -Force)",
    ),
    (
        r"(?i)\bdiskpart\b",
        "Low-level disk partitioning tool (diskpart)",
    ),
    (
        r"(?i)\bshutdown(\s+.*)?\b",
        "System shutdown or restart (shutdown)",
    ),
    (
        r"(?i)\breg\s+delete\b",
        "Windows registry key deletion (reg delete)",
    ),
    (
        r"(?i)\b(drop\s+database|drop\s+table)\b",
        "Database destruction statement",
    ),
    (
        r"(?i)\b(bcdedit|wbadmin)\b",
        "Boot configuration or system backup modification",
    ),
]


def is_dangerous_command(command: str) -> Tuple[bool, str]:
    """
    Scans a command against dangerous system patterns.

    Args:
        command: The raw command string.

    Returns:
        Tuple of (is_dangerous, reason_description).
    """
    clean_cmd = command.strip()
    if not clean_cmd:
        return False, ""

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, clean_cmd):
            return True, description

    return False, ""
