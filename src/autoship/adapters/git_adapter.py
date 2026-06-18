"""Adapter for Git operations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from autoship.exceptions import GitError


class GitAdapter:
    """Thin wrapper around Git subprocess calls."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def _run(
        self,
        cmd: list[str],
        *,
        check: bool = True,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                cmd,
                cwd=self.repo_root,
                check=check,
                capture_output=capture_output,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise GitError(
                f"Git command failed: {' '.join(cmd)}",
                details={"cmd": cmd, "returncode": exc.returncode, "stderr": exc.stderr},
            ) from exc

    def has_changes(self) -> bool:
        """Return True if the working tree has staged or unstaged changes."""
        result = self._run(["git", "status", "--porcelain"], check=False)
        return result.stdout.strip() != ""

    def diff(self) -> str:
        """Return the full diff of unstaged changes."""
        result = self._run(["git", "diff"])
        return result.stdout

    def stats(self) -> str:
        """Return a short diff stat summary."""
        result = self._run(["git", "diff", "--stat"])
        return result.stdout

    def commit(self, message: str) -> None:
        """Stage all changes and commit with the given message."""
        self._run(["git", "add", "-A"])
        self._run(["git", "commit", "-m", message])
