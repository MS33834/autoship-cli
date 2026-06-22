"""Integration tests for the Docker upload adapter."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from autoship.adapters.upload.docker import DockerUploader
from autoship.exceptions import UploadError


def _write_docker_project(root: Path) -> None:
    """Create a minimal Docker project in the temporary root."""
    (root / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")


def test_docker_dry_run(tmp_path: Path) -> None:
    uploader = DockerUploader(tmp_path, image="myapp", tag="latest")
    result = uploader.upload(dry_run=True)
    assert result.success is True
    assert result.target == "docker"
    assert result.details["dry_run"] is True
    assert result.details["image"] == "myapp:latest"


def test_docker_validate_missing_cli(tmp_path: Path) -> None:
    uploader = DockerUploader(tmp_path, image="myapp")
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(UploadError, match="docker` CLI not found"),
    ):
        uploader.validate()


def test_docker_upload_success(tmp_path: Path) -> None:
    _write_docker_project(tmp_path)
    uploader = DockerUploader(tmp_path, image="myapp", tag="v1")
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        result = uploader.upload()

    assert result.success is True
    assert result.target == "docker"
    assert result.details["image"] == "myapp:v1"
    assert mock_run.call_count == 2

    build_call, push_call = mock_run.call_args_list
    assert build_call.args[0] == ["docker", "build", "-t", "myapp:v1", "."]
    assert build_call.kwargs["cwd"] == tmp_path
    assert build_call.kwargs["check"] is True
    assert push_call.args[0] == ["docker", "push", "myapp:v1"]
    assert push_call.kwargs["cwd"] == tmp_path
    assert push_call.kwargs["check"] is True


def test_docker_upload_with_registry(tmp_path: Path) -> None:
    _write_docker_project(tmp_path)
    uploader = DockerUploader(tmp_path, image="myapp", tag="v1", registry="localhost:5000")
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        result = uploader.upload()

    assert result.success is True
    assert result.details["image"] == "localhost:5000/myapp:v1"
    assert mock_run.call_count == 2

    build_call, push_call = mock_run.call_args_list
    assert build_call.args[0] == ["docker", "build", "-t", "localhost:5000/myapp:v1", "."]
    assert push_call.args[0] == ["docker", "push", "localhost:5000/myapp:v1"]


def test_docker_upload_failure_raises_upload_error(tmp_path: Path) -> None:
    _write_docker_project(tmp_path)
    uploader = DockerUploader(tmp_path, image="myapp", tag="v1")

    def _fail_build(*_args, **_kwargs) -> None:
        raise subprocess.CalledProcessError(1, ["docker", "build"])

    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run", side_effect=_fail_build),
        pytest.raises(UploadError, match="Docker upload failed"),
    ):
        uploader.upload()


def test_docker_upload_verbose_prints_commands(tmp_path: Path, capsys) -> None:
    _write_docker_project(tmp_path)
    uploader = DockerUploader(tmp_path, image="myapp", tag="v1")
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        uploader.upload(verbose=True)

    captured = capsys.readouterr()
    assert "docker build -t myapp:v1 ." in captured.out
    assert "docker push myapp:v1" in captured.out
    assert mock_run.call_count == 2
