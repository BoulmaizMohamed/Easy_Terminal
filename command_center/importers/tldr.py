"""tldr-pages importer and offline synchronizer for Command Center."""

from __future__ import annotations

import io
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from command_center.db import get_connection

TLDR_ZIP_URL = "https://github.com/tldr-pages/tldr/releases/latest/download/tldr.zip"

CATEGORY_KEYWORDS = {
    "Network": ["net", "ping", "ip", "dns", "http", "curl", "ssh", "socket", "port", "route", "tcp", "udp", "arp", "traceroute", "tracert", "nslookup", "ftp", "adapter", "wifi"],
    "Files": ["file", "dir", "copy", "cat", "find", "grep", "tar", "zip", "tree", "move", "rename", "chmod", "attrib", "robocopy", "format", "archive", "compress", "expand", "tail", "head"],
    "Processes": ["process", "task", "kill", "ps", "top", "job", "pid", "taskkill", "tasklist", "priority"],
    "Disk": ["disk", "volume", "mount", "drive", "chkdsk", "fsutil", "partition", "storage", "quota", "cleanmgr"],
    "Users": ["user", "group", "who", "id", "perm", "sudo", "runas", "whoami", "session", "logon", "password"],
    "Services": ["service", "daemon", "sc", "systemctl", "init", "start", "stop", "spooler"],
    "Search": ["search", "where", "which", "locate", "select-string", "findstr", "query"],
    "System": ["system", "os", "shutdown", "reboot", "time", "date", "uptime", "hostname", "sfc", "info", "battery", "power", "env", "var", "hardware"],
}


def map_category(title: str, description: str, command: str) -> str:
    """Classifies a command into a category using keyword matching."""
    text = f"{title} {description} {command}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "General"


def parse_tldr_content(content: str, platform: str = "windows") -> List[Dict[str, Any]]:
    """
    Parses a tldr markdown page into individual command entries.

    Format:
        # command
        > description
        - example description
        `example command`
    """
    lines = content.splitlines()
    cmd_title = ""
    desc_lines: List[str] = []
    examples: List[Tuple[str, str]] = []

    current_example_desc: Optional[str] = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("# ") and not cmd_title:
            cmd_title = line[2:].strip()
        elif line.startswith("> ") and not examples and current_example_desc is None:
            desc_text = line[2:].strip()
            # Clean off "More information:" links if desired
            if not desc_text.lower().startswith("more information:"):
                desc_lines.append(desc_text)
        elif line.startswith("- "):
            current_example_desc = line[2:].rstrip(":")
        elif line.startswith("`") and line.endswith("`") and current_example_desc is not None:
            cmd_text = line[1:-1].strip()
            examples.append((current_example_desc, cmd_text))
            current_example_desc = None

    page_description = " ".join(desc_lines).strip()
    shell = "cmd" if platform == "windows" else "both"
    results: List[Dict[str, Any]] = []

    for ex_desc, ex_cmd in examples:
        name = f"{cmd_title}: {ex_desc}"
        cat = map_category(cmd_title, ex_desc, ex_cmd)
        results.append(
            {
                "name": name,
                "command": ex_cmd,
                "shell": shell,
                "category": cat,
                "description": page_description or ex_desc,
                "example": ex_cmd,
                "tags": f"tldr,{cmd_title}",
                "source": "tldr",
            }
        )

    return results


def sync_tldr_pages(
    db_path: Optional[str | Path] = None,
    max_pages: Optional[int] = None,
    on_progress: Optional[Callable[[str], None]] = None,
    custom_zip_data: Optional[bytes] = None,
) -> Tuple[int, int]:
    """
    Downloads tldr.zip and upserts source='tldr' commands into SQLite.
    Never overwrites user entries or resets usage counts for existing rows.

    Returns:
        Tuple of (newly_added_count, updated_count).
    """
    if custom_zip_data:
        zip_bytes = custom_zip_data
    else:
        if on_progress:
            on_progress("Downloading latest tldr-pages archive...")
        req = urllib.request.Request(TLDR_ZIP_URL, headers={"User-Agent": "CommandCenter/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            zip_bytes = resp.read()

    if on_progress:
        on_progress("Extracting Windows and common command pages...")

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    all_names = zf.namelist()

    win_files = [n for n in all_names if "pages/windows/" in n and n.endswith(".md")]
    common_files = [n for n in all_names if "pages/common/" in n and n.endswith(".md")]

    selected_files: List[Tuple[str, str]] = [(f, "windows") for f in win_files]
    # Include popular common tools as well
    if max_pages is not None:
        remaining = max_pages - len(selected_files)
        if remaining > 0:
            selected_files.extend([(f, "common") for f in common_files[:remaining]])
    else:
        selected_files.extend([(f, "common") for f in common_files])

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    added = 0
    updated = 0

    with conn:
        for idx, (path_in_zip, platform) in enumerate(selected_files):
            try:
                content = zf.read(path_in_zip).decode("utf-8", errors="replace")
                entries = parse_tldr_content(content, platform=platform)
            except Exception:
                continue

            for entry in entries:
                # Upsert into library with source='tldr'
                # Preserves user entries, use_count, favorite, and last_used_at
                cursor = conn.execute(
                    """
                    INSERT INTO library (name, command, shell, category, description, example, tags, favorite, use_count, source, date_added, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'tldr', ?, ?)
                    ON CONFLICT(command, shell, source) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        example = excluded.example,
                        category = excluded.category,
                        updated_at = excluded.updated_at
                    """,
                    (
                        entry["name"],
                        entry["command"],
                        entry["shell"],
                        entry["category"],
                        entry["description"],
                        entry["example"],
                        entry["tags"],
                        now,
                        now,
                    ),
                )
                if cursor.rowcount == 1:
                    added += 1
                elif cursor.rowcount > 1:
                    updated += 1

            if on_progress and idx % 50 == 0:
                on_progress(f"Processed {idx}/{len(selected_files)} pages...")

    conn.close()
    if on_progress:
        on_progress(f"Sync complete: {added} added, {updated} updated.")
    return added, updated


def cmdlet_importer_hook(source_data: Any) -> List[Dict[str, Any]]:
    """Hook for future official PowerShell cmdlet documentation importer."""
    return []
