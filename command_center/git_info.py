"""Repository and root location detection helper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LocationInfo:
    """Information about current working directory and Git repository."""

    cwd: str
    is_git: bool = False
    repo_name: str = ""
    branch: str = ""
    subpath: str = ""
    root: str = ""
    repo_root: str = ""

    def get_prompt_badge(self) -> str:
        """Compact indicator for the prompt line."""
        if self.is_git:
            branch_str = f"({self.branch})" if self.branch else ""
            sub = self.subpath if self.subpath else ""
            parts = [f"📁 {self.repo_name}{sub}"]
            if branch_str:
                parts.append(branch_str)
            return " ".join(parts)
        folder = Path(self.cwd).name or self.cwd
        return f"📁 {folder}"

    def get_repo_badge(self, lang: str = "en") -> str:
        """Status bar badge for repository or root."""
        if self.is_git:
            repo_label = "Dépôt" if lang == "fr" else "Repo"
            branch_str = f" [{self.branch}]" if self.branch else ""
            return f"🌿 {repo_label}: {self.repo_name}{branch_str}"
        root_label = "Racine" if lang == "fr" else "Root"
        return f"({root_label}: {self.root})"


def get_location_info(cwd: Optional[str] = None) -> LocationInfo:
    """Detects Git repository and drive root without external subprocess calls."""
    if not cwd:
        cwd = os.getcwd()

    try:
        p = Path(cwd).resolve()
    except Exception:
        p = Path(cwd)

    drive, _ = os.path.splitdrive(str(p))
    root_str = (drive + "\\") if drive else "\\"

    try:
        # Walk parent directories to check for .git
        user_home = Path.home().resolve()
        search_dirs = [p] + list(p.parents)
        for parent in search_dirs:
            # If the user has a bare or accidental .git in their home profile directory,
            # don't treat every subdirectory in their entire system as that repo unless cwd is home.
            if parent == user_home and p != user_home:
                continue

            git_entry = parent / ".git"
            if git_entry.exists():
                repo_name = parent.name
                branch = ""
                head_file: Optional[Path] = None

                if git_entry.is_dir():
                    head_file = git_entry / "HEAD"
                elif git_entry.is_file():  # worktree or submodule
                    try:
                        content = git_entry.read_text("utf-8", errors="ignore").strip()
                        if content.startswith("gitdir:"):
                            gitdir_path = Path(content.split(":", 1)[1].strip())
                            if not gitdir_path.is_absolute():
                                gitdir_path = parent / gitdir_path
                            head_file = gitdir_path / "HEAD"
                    except Exception:
                        pass

                if head_file and head_file.exists():
                    try:
                        ref = head_file.read_text("utf-8", errors="ignore").strip()
                        if ref.startswith("ref: refs/heads/"):
                            branch = ref[16:]
                        elif ref:
                            branch = ref[:7]
                    except Exception:
                        pass

                rel = p.relative_to(parent)
                sub = "" if str(rel) == "." else f"/{rel.as_posix()}"
                return LocationInfo(
                    cwd=str(p),
                    is_git=True,
                    repo_name=repo_name,
                    branch=branch,
                    subpath=sub,
                    root=root_str,
                    repo_root=str(parent),
                )
    except Exception:
        pass

    return LocationInfo(
        cwd=str(p),
        is_git=False,
        repo_name="",
        branch="",
        subpath="",
        root=root_str,
        repo_root="",
    )


def record_repository(
    path: str,
    name: str,
    branch: str = "",
    db_path: Optional[str | Path] = None,
) -> None:
    """Records or updates a visited repository in the SQLite database."""
    try:
        from command_center.db import get_connection

        conn = get_connection(db_path)
        now_iso = datetime.now(timezone.utc).isoformat()
        with conn:
            conn.execute(
                """
                INSERT INTO repositories (path, name, branch, last_visited_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    name = excluded.name,
                    branch = excluded.branch,
                    last_visited_at = excluded.last_visited_at
                """,
                (str(Path(path).resolve()), name, branch, now_iso),
            )
        conn.close()
    except Exception:
        pass


def get_known_repositories(
    cwd: Optional[str] = None,
    db_path: Optional[str | Path] = None,
    scan_neighbors: bool = True,
) -> List[Dict[str, Any]]:
    """Returns sorted list of known Git repositories, merging DB records and local discovery."""
    repos: Dict[str, Dict[str, Any]] = {}

    # 1. Load from DB
    try:
        from command_center.db import get_connection

        conn = get_connection(db_path)
        rows = conn.execute(
            "SELECT path, name, branch, last_visited_at FROM repositories ORDER BY last_visited_at DESC"
        ).fetchall()
        for r in rows:
            p = str(Path(r["path"]).resolve())
            if Path(p).exists():
                repos[p] = {
                    "path": p,
                    "name": r["name"],
                    "branch": r["branch"] or "",
                    "last_visited_at": r["last_visited_at"],
                }
        conn.close()
    except Exception:
        pass

    # 2. Add current cwd if it's a git repo
    active_loc = get_location_info(cwd)
    if active_loc.is_git and active_loc.repo_root:
        root_path = str(Path(active_loc.repo_root).resolve())
        if root_path not in repos:
            repos[root_path] = {
                "path": root_path,
                "name": active_loc.repo_name,
                "branch": active_loc.branch,
                "last_visited_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            repos[root_path]["branch"] = active_loc.branch

    # 3. Discover sibling/neighbor repositories
    if scan_neighbors:
        scan_bases = []
        if active_loc.is_git and active_loc.repo_root:
            parent_dir = Path(active_loc.repo_root).parent
            if parent_dir.exists():
                scan_bases.append(parent_dir)
        elif cwd:
            scan_bases.append(Path(cwd).resolve())

        try:
            desktop = Path.home() / "Desktop"
            if desktop.exists() and desktop not in scan_bases:
                scan_bases.append(desktop)
        except Exception:
            pass

        for base in scan_bases:
            try:
                for entry in base.iterdir():
                    if entry.is_dir() and not entry.name.startswith("."):
                        candidate = str(entry.resolve())
                        if candidate not in repos and (entry / ".git").exists():
                            loc = get_location_info(candidate)
                            if loc.is_git:
                                repos[candidate] = {
                                    "path": candidate,
                                    "name": loc.repo_name or entry.name,
                                    "branch": loc.branch,
                                    "last_visited_at": "",
                                }
            except Exception:
                pass

    return list(repos.values())


def find_repository(
    query: str,
    cwd: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> Optional[Dict[str, Any]]:
    """Finds a matching repository by exact name, prefix, substring, or directory path."""
    query_clean = query.strip()
    if not query_clean:
        return None

    # Check if direct directory path
    p = Path(query_clean)
    if p.exists() and p.is_dir():
        loc = get_location_info(str(p))
        if loc.is_git and loc.repo_root:
            return {"name": loc.repo_name, "path": loc.repo_root, "branch": loc.branch}

    known = get_known_repositories(cwd=cwd, db_path=db_path)
    q_lower = query_clean.lower()

    # Exact name match
    for r in known:
        if r["name"].lower() == q_lower:
            return r

    # Prefix match
    for r in known:
        if r["name"].lower().startswith(q_lower):
            return r

    # Substring match
    for r in known:
        if q_lower in r["name"].lower():
            return r

    return None
