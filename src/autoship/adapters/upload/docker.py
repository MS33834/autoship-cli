"""Docker build/push adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path

from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.core.tool_verifier import ToolVerifier
from autoship.exceptions import UploadError
from autoship.models.config import ToolsConfig


class DockerUploader(UploadAdapter):
    """Build and push a Docker image."""

    name = "docker"

    def __init__(
        self,
        project_root: Path,
        image: str,
        tag: str = "latest",
        *,
        registry: str | None = None,
        tool_verifier: ToolVerifier | None = None,
    ) -> None:
        self.project_root = project_root
        self.image = image
        self.tag = tag
        self.registry = registry
        self._verifier = tool_verifier or ToolVerifier(ToolsConfig())

    @property
    def full_image(self) -> str:
        """Return the fully qualified image name including registry prefix."""
        if self.registry:
            return f"{self.registry.rstrip('/')}/{self.image}:{self.tag}"
        return f"{self.image}:{self.tag}"

    def validate(self) -> None:
        """Ensure Docker CLI is available."""
        if not self._verifier.check("docker"):
            raise UploadError("`docker` CLI not found for Docker upload")

    def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
        """Build and push the configured image."""
        full_image = self.full_image
        details: dict[str, object] = {"image": full_image}
        if dry_run:
            details["dry_run"] = True
            return UploadResult(
                success=True,
                target=self.name,
                details=details,
            )

        self.validate()

        try:
            docker = self._verifier.resolve("docker")
            build_cmd = [docker, "build", "-t", full_image, "."]
            push_cmd = [docker, "push", full_image]
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
            details=details,
        )
