"""GitHub release adapter."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.exceptions import UploadError


class GitHubUploader(UploadAdapter):
    """Create a GitHub release and upload artifacts."""

    name = "github"

    def __init__(self, project_root: Path, tag: str, artifacts: list[str] | None = None) -> None:
        self.project_root = project_root
        self.tag = tag
        self.artifacts = artifacts or ["dist/*"]

    def validate(self) -> None:
        """Ensure GitHub CLI is available."""
        if not shutil.which("gh"):
            raise UploadError("`gh` CLI not found for GitHub release upload")

    def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
        """Create a GitHub release and attach artifacts."""
        if dry_run:
            return UploadResult(
                success=True,
                target=self.name,
                details={"tag": self.tag, "artifacts": self.artifacts, "dry_run": True},
            )

        self.validate()

        try:
            create_cmd = ["gh", "release", "create", self.tag, "--generate-notes"]
            upload_cmd = ["gh", "release", "upload", self.tag, *self.artifacts]
            if verbose:
                print(f"[exec] {' '.join(create_cmd)}")
                print(f"[exec] {' '.join(upload_cmd)}")
            subprocess.run(create_cmd, cwd=self.project_root, check=True)
            subprocess.run(upload_cmd, cwd=self.project_root, check=True)
        except subprocess.CalledProcessError as exc:
            raise UploadError(f"GitHub release failed: {exc}") from exc

        return UploadResult(
            success=True,
            target=self.name,
            url=f"https://github.com/release/{self.tag}",
            details={"tag": self.tag, "artifacts": self.artifacts},
        )
