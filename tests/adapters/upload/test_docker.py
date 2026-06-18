"""Tests for the Docker upload adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoship.adapters.upload.docker import DockerUploader
from autoship.exceptions import UploadError


def test_docker_dry_run(project_root: Path) -> None:
    uploader = DockerUploader(project_root, image="myapp", tag="latest")
    result = uploader.upload(dry_run=True)
    assert result.success is True
    assert result.target == "docker"
    assert result.details["dry_run"] is True


def test_docker_validate_missing_cli(project_root: Path) -> None:
    uploader = DockerUploader(project_root, image="myapp")
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(UploadError, match="docker` CLI not found"),
    ):
        uploader.validate()


def test_docker_upload_success(project_root: Path) -> None:
    uploader = DockerUploader(project_root, image="myapp", tag="v1")
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        result = uploader.upload()
    assert result.success is True
    assert result.details["image"] == "myapp:v1"
    assert mock_run.call_count == 2
