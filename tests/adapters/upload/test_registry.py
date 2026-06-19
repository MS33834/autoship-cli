"""Tests for the upload adapter registry/factory.

Note:
    ``src/autoship/adapters/upload/registry.py`` is currently a factory that
    maps upload target names (``pypi``, ``docker``, ``github``) to adapter
    instances. There is no HTTP-based plugin registry upload adapter
    (``httpx.Client.post``) implemented yet, so this module tests the
    factory functions only and documents that gap.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoship.adapters.upload import get_uploader
from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.adapters.upload.docker import DockerUploader
from autoship.adapters.upload.github import GitHubUploader
from autoship.adapters.upload.pypi import PyPIUploader
from autoship.adapters.upload.registry import register_uploader
from autoship.exceptions import ConfigError


def test_get_pypi_uploader(tmp_path: Path) -> None:
    uploader = get_uploader("pypi", tmp_path)
    assert isinstance(uploader, PyPIUploader)
    assert uploader.project_root == tmp_path


def test_get_docker_uploader_requires_image(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="requires '--image'"):
        get_uploader("docker", tmp_path)

    uploader = get_uploader("docker", tmp_path, {"image": "myapp"})
    assert isinstance(uploader, DockerUploader)
    assert uploader.image == "myapp"
    assert uploader.tag == "latest"


def test_get_docker_uploader_accepts_tag(tmp_path: Path) -> None:
    uploader = get_uploader("docker", tmp_path, {"image": "myapp", "tag": "v2"})
    assert isinstance(uploader, DockerUploader)
    assert uploader.tag == "v2"


def test_get_github_uploader_requires_tag(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="requires '--tag'"):
        get_uploader("github", tmp_path)

    uploader = get_uploader("github", tmp_path, {"tag": "v1.0.0"})
    assert isinstance(uploader, GitHubUploader)
    assert uploader.tag == "v1.0.0"


def test_get_github_uploader_accepts_artifacts(tmp_path: Path) -> None:
    uploader = get_uploader(
        "github",
        tmp_path,
        {"tag": "v1.0.0", "artifacts": ["dist/*", "build/*"]},
    )
    assert isinstance(uploader, GitHubUploader)
    assert uploader.artifacts == ["dist/*", "build/*"]


def test_get_unknown_uploader_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Unknown upload target"):
        get_uploader("unknown", tmp_path)


def test_register_custom_uploader(tmp_path: Path) -> None:
    class CustomUploader(UploadAdapter):
        name = "custom"

        def validate(self) -> None:
            pass

        def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
            return UploadResult(success=True, target="custom")

    register_uploader("custom", lambda root, cfg: CustomUploader())
    uploader = get_uploader("custom", tmp_path)
    assert isinstance(uploader, CustomUploader)
