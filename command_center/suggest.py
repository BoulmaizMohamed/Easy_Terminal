"""Command auto-suggest engine for Command Center."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from command_center.db import get_connection


@dataclass
class Suggestion:
    """Represents a single command suggestion."""

    command: str
    description: str = ""
    source: str = "history"
    count: int = 1
    favorite: bool = False
    score: float = 0.0


def _get_path_suggestions(query: str, cwd: Optional[str | Path]) -> List[Suggestion]:
    """Generates file and directory completion suggestions like cmd.exe."""
    if not cwd or not query.strip():
        return []

    parts = query.rsplit(" ", 1)
    prefix = (parts[0] + " ") if len(parts) > 1 else ""
    token = parts[-1]

    token_dir, _, token_file = token.rpartition("\\")
    if not token_dir:
        token_dir, _, token_file = token.rpartition("/")

    try:
        search_dir = Path(cwd) / token_dir if token_dir else Path(cwd)
        if not search_dir.exists() or not search_dir.is_dir():
            return []
    except Exception:
        return []

    results: List[Suggestion] = []
    target = token_file.lower()
    try:
        for entry in os.scandir(search_dir):
            if entry.name.lower().startswith(target):
                sub = (token_dir + "\\" if token_dir else "") + entry.name
                if entry.is_dir():
                    sub += "\\"
                desc = "Directory" if entry.is_dir() else "File"
                results.append(
                    Suggestion(
                        command=prefix + sub,
                        description=desc,
                        source="path",
                        count=1,
                        favorite=False,
                        score=850.0,
                    )
                )
    except Exception:
        pass
    return results[:10]


def rank_suggestions(
    query: str,
    shell: str,
    db_path: Optional[str | Path] = None,
    limit: int = 8,
    cwd: Optional[str | Path] = None,
) -> List[Suggestion]:
    """
    Ranks auto-suggestions based on prefix/substring match, frequency, recency, and favorites.

    Args:
        query: User typed query string.
        shell: Active shell ('powershell' or 'cmd').
        db_path: Optional SQLite database path.
        limit: Max suggestions to return (default 8).

    Returns:
        List of Suggestion objects sorted by descending relevance.
    """
    clean_query = query.strip().lower()
    if not clean_query:
        return []

    conn = get_connection(db_path)
    now = datetime.now(timezone.utc)

    # 1. Fetch candidates from history
    hist_query = """
        SELECT command, COUNT(*) as count, MAX(ran_at) as last_ran
        FROM history
        WHERE shell = ? AND command LIKE ?
        GROUP BY command
        ORDER BY count DESC
        LIMIT 50
    """
    like_pattern = f"%{clean_query}%"
    cursor = conn.execute(hist_query, (shell.lower(), like_pattern))
    history_candidates = cursor.fetchall()

    # 2. Fetch candidates from library (for shell or 'both')
    lib_query = """
        SELECT command, description, use_count, last_used_at, favorite
        FROM library
        WHERE (shell = ? OR shell = 'both') AND command LIKE ?
        ORDER BY favorite DESC, use_count DESC
        LIMIT 50
    """
    cursor = conn.execute(lib_query, (shell.lower(), like_pattern))
    library_candidates = cursor.fetchall()
    conn.close()

    candidates_map: Dict[str, Suggestion] = {}

    # Process history candidates
    for row in history_candidates:
        cmd = row["command"]
        count = row["count"]
        last_ran_str = row["last_ran"]
        days_ago = 30.0
        if last_ran_str:
            try:
                dt = datetime.fromisoformat(last_ran_str.replace("Z", "+00:00"))
                days_ago = max(0.0, (now - dt).total_seconds() / 86400.0)
            except Exception:
                pass

        score = _compute_score(cmd, clean_query, count, days_ago, favorite=False)
        candidates_map[cmd] = Suggestion(
            command=cmd,
            source="history",
            count=count,
            score=score,
        )

    # Process library candidates (merge with history if identical command)
    for row in library_candidates:
        cmd = row["command"]
        desc = row["description"] or ""
        use_count = row["use_count"] or 0
        fav = bool(row["favorite"])
        last_used_str = row["last_used_at"]
        days_ago = 30.0
        if last_used_str:
            try:
                dt = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
                days_ago = max(0.0, (now - dt).total_seconds() / 86400.0)
            except Exception:
                pass

        lib_score = _compute_score(cmd, clean_query, use_count, days_ago, favorite=fav)

        if cmd in candidates_map:
            # Existing history match: enrich with library metadata and favor boost
            existing = candidates_map[cmd]
            existing.description = desc
            existing.favorite = fav
            existing.score = max(existing.score, lib_score) + (300.0 if fav else 0.0)
        else:
            candidates_map[cmd] = Suggestion(
                command=cmd,
                description=desc,
                source="library",
                count=use_count,
                favorite=fav,
                score=lib_score,
            )

    # 3. Path & file completion candidates from cwd (like cmd.exe)
    if cwd:
        for p in _get_path_suggestions(clean_query, cwd):
            if p.command not in candidates_map:
                candidates_map[p.command] = p

    # Sort candidates by score descending
    sorted_suggestions = sorted(
        candidates_map.values(),
        key=lambda s: s.score,
        reverse=True,
    )

    return sorted_suggestions[:limit]


def _compute_score(
    command: str,
    query: str,
    frequency: int,
    days_ago: float,
    favorite: bool,
) -> float:
    """Computes relevance score for ranking."""
    cmd_lower = command.lower()
    # Match type scoring
    if cmd_lower.startswith(query):
        # Prefix matches get highest base score; shorter matching commands preferred
        base_match = 1000.0 - min(len(command), 100)
    elif query in cmd_lower:
        # Substring matches get moderate base score
        idx = cmd_lower.find(query)
        base_match = 400.0 - min(idx * 5, 100)
    else:
        return 0.0

    # Frequency factor
    freq_score = min(frequency * 15.0, 300.0)

    # Recency decay: highest boost if used today, decreasing over days
    recency_score = 250.0 / (1.0 + days_ago)

    # Favorite bonus
    fav_score = 500.0 if favorite else 0.0

    return base_match + freq_score + recency_score + fav_score
