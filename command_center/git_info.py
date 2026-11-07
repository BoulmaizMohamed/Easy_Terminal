"""Repository and root location detection helper."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LocationInfo:
    """Information about current working directory and Git repository."""

    cwd: str
    is_git: bool = False
    repo_name: str = ""
    branch: str = ""
    subpath: str = ""
    root: str = ""

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
    )
