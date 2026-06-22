"""Upload adapter registry/factory."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from autoship.adapters.upload.base import UploadAdapter
from autoship.adapters.upload.docker import DockerUploader
from autoship.adapters.upload.github import GitHubUploader
from autoship.adapters.upload.pypi import PyPIUploader
from autoship.exceptions import ConfigError

_Registry = dict[str, Callable[[Path, dict[str, Any]], UploadAdapter]]


def _docker_factory(root: Path, cfg: dict[str, Any]) -> DockerUploader:
    image = cfg.get("image")
    if not image:
        raise ConfigError("Upload target 'docker' requires '--image'")
    return DockerUploader(
        root,
        image=image,
        tag=cfg.get("tag", "latest"),
        registry=cfg.get("registry"),
    )


def _github_factory(root: Path, cfg: dict[str, Any]) -> GitHubUploader:
    tag = cfg.get("tag")
    if not tag:
        raise ConfigError("Upload target 'github' requires '--tag'")
    return GitHubUploader(
        root,
        tag=tag,
        artifacts=cfg.get("artifacts"),
    )


_UPLOADERS: _Registry = {
    "pypi": lambda root, cfg: PyPIUploader(
        root,
        repository=cfg.get("repository", "testpypi"),
        repository_url=cfg.get("repository_url"),
    ),
    "docker": _docker_factory,
    "github": _github_factory,
}


def register_uploader(name: str, factory: Callable[[Path, dict[str, Any]], UploadAdapter]) -> None:
    """Register a custom upload adapter factory."""
    _UPLOADERS[name] = factory


def get_uploader(name: str, project_root: Path, cfg: dict[str, Any] | None = None) -> UploadAdapter:
    """Return an upload adapter instance for the named target."""
    if name not in _UPLOADERS:
        raise ConfigError(f"Unknown upload target: {name}")
    return _UPLOADERS[name](project_root, cfg or {})
