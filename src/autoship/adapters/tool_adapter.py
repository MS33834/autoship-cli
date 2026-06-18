"""Adapter for running external formatting/cleanup tools."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class ToolChain:
    """Run a configurable sequence of cleanup/formatting tools."""

    def __init__(
        self,
        tools: list[str],
        project_root: Path,
        *,
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        self.tools = tools
        self.project_root = project_root
        self.dry_run = dry_run
        self.verbose = verbose

    def _run(
        self,
        cmd: list[str],
        *,
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        if self.dry_run:
            print(f"[dry-run] {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")
        if self.verbose:
            print(f"[exec] {' '.join(cmd)}")
        return subprocess.run(
            cmd,
            cwd=self.project_root,
            check=check,
            capture_output=capture_output,
            text=True,
        )

    def preview(self, paths: list[Path]) -> str:
        """Return a diff/preview of the changes that would be applied."""
        targets = [str(p) for p in paths]
        if "black" in self.tools and shutil.which("black"):
            result = self._run(["black", "--diff"] + targets, capture_output=True)
            return result.stdout
        return ""

    def apply(self, paths: list[Path]) -> None:
        """Apply formatting/cleanup tools in place."""
        targets = [str(p) for p in paths]
        if "autoflake" in self.tools and shutil.which("autoflake"):
            self._run(
                ["autoflake", "--remove-all-unused-imports", "--in-place", "-r"] + targets,
            )
        if "black" in self.tools and shutil.which("black"):
            self._run(["black"] + targets)
