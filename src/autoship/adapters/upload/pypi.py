"""PyPI upload adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.core.tool_verifier import ToolVerifier
from autoship.exceptions import UploadError
from autoship.models.config import ToolsConfig


class PyPIUploader(UploadAdapter):
    """Publish Python packages to PyPI or TestPyPI."""

    name = "pypi"

    def __init__(
        self,
        project_root: Path,
        repository: str = "pypi",
        *,
        tool_verifier: ToolVerifier | None = None,
    ) -> None:
        self.project_root = project_root
        self.repository = repository
        self._verifier = tool_verifier or ToolVerifier(ToolsConfig())

    def validate(self) -> None:
        """Ensure build tooling is installed."""
        for tool in ("python", "twine"):
            if not self._verifier.check(tool):
                raise UploadError(f"Required tool `{tool}` not found for PyPI upload")

    def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
        """Build and upload distribution artifacts."""
        if dry_run:
            return UploadResult(
                success=True,
                target=self.name,
                details={"repository": self.repository, "dry_run": True},
            )

        self.validate()

        try:
            python = self._verifier.resolve("python")
            twine = self._verifier.resolve("twine")
            subprocess.run(
                [python, "-m", "build", "--sdist", "--wheel"],
                cwd=self.project_root,
                check=True,
            )
            dist_dir = self.project_root / "dist"
            artifacts = sorted(dist_dir.glob("*"))
            if not artifacts:
                raise UploadError("No distribution artifacts found in dist/")
            cmd = [twine, "upload", "--repository", self.repository]
            cmd.extend(str(path) for path in artifacts)
            if verbose:
                print(f"[exec] {' '.join(cmd)}")
            subprocess.run(cmd, cwd=self.project_root, check=True, shell=False)
        except subprocess.CalledProcessError as exc:
            raise UploadError(f"PyPI upload failed: {exc}") from exc

        return UploadResult(
            success=True,
            target=self.name,
            details={"repository": self.repository},
        )
