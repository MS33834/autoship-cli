"""Docker build/push adapter."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.exceptions import UploadError


class DockerUploader(UploadAdapter):
    """Build and push a Docker image."""

    name = "docker"

    def __init__(self, project_root: Path, image: str, tag: str = "latest") -> None:
        self.project_root = project_root
        self.image = image
        self.tag = tag

    def validate(self) -> None:
        """Ensure Docker CLI is available."""
        if not shutil.which("docker"):
            raise UploadError("`docker` CLI not found for Docker upload")

    def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
        """Build and push the configured image."""
        full_image = f"{self.image}:{self.tag}"
        if dry_run:
            return UploadResult(
                success=True,
                target=self.name,
                details={"image": full_image, "dry_run": True},
            )

        self.validate()

        try:
            build_cmd = ["docker", "build", "-t", full_image, "."]
            push_cmd = ["docker", "push", full_image]
            if verbose:
                print(f"[exec] {' '.join(build_cmd)}")
                print(f"[exec] {' '.join(push_cmd)}")
            subprocess.run(build_cmd, cwd=self.project_root, check=True)
            subprocess.run(push_cmd, cwd=self.project_root, check=True)
        except subprocess.CalledProcessError as exc:
            raise UploadError(f"Docker upload failed: {exc}") from exc

        return UploadResult(
            success=True,
            target=self.name,
            details={"image": full_image},
        )
