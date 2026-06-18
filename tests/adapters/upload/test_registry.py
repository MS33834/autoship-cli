"""Tests for upload adapter registry."""

from __future__ import annotations

import pytest

from autoship.adapters.upload import get_uploader
from autoship.adapters.upload.base import UploadAdapter, UploadResult
from autoship.adapters.upload.docker import DockerUploader
from autoship.adapters.upload.github import GitHubUploader
from autoship.adapters.upload.pypi import PyPIUploader
from autoship.adapters.upload.registry import register_uploader
from autoship.exceptions import ConfigError


def test_get_pypi_uploader(project_root) -> None:
    uploader = get_uploader("pypi", project_root)
    assert isinstance(uploader, PyPIUploader)


def test_get_docker_uploader_requires_image(project_root) -> None:
    uploader = get_uploader("docker", project_root, {"image": "myapp"})
    assert isinstance(uploader, DockerUploader)
    assert uploader.image == "myapp"


def test_get_github_uploader_requires_tag(project_root) -> None:
    uploader = get_uploader("github", project_root, {"tag": "v1.0.0"})
    assert isinstance(uploader, GitHubUploader)
    assert uploader.tag == "v1.0.0"


def test_get_unknown_uploader_raises(project_root) -> None:
    with pytest.raises(ConfigError):
        get_uploader("unknown", project_root)


def test_register_custom_uploader(project_root) -> None:
    class CustomUploader(UploadAdapter):
        name = "custom"

        def validate(self) -> None:
            pass

        def upload(self, *, dry_run: bool = False, verbose: bool = False) -> UploadResult:
            return UploadResult(success=True, target="custom")

    register_uploader("custom", lambda root, cfg: CustomUploader())
    uploader = get_uploader("custom", project_root)
    assert isinstance(uploader, CustomUploader)
