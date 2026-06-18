"""Tests for the built-in docker-ship plugin."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from autoship.core.context import CommandContext
from autoship.exceptions import UploadError
from autoship.models.config import AppConfig, DockerShipConfig
from autoship.plugins import docker_ship


@pytest.fixture
def docker_context(app_config: AppConfig) -> CommandContext:
    """Return a CommandContext for a Docker upload."""
    app_config.docker_ship = DockerShipConfig(enabled=True, default_image="myapp")
    return CommandContext(
        command="upload",
        project_root=app_config.project_root,
        config=app_config,
        extras={"target": "docker", "tag": "v1"},
    )


def test_docker_ship_skips_non_docker_target(docker_context: CommandContext) -> None:
    docker_context.extras["target"] = "pypi"
    with patch("subprocess.run") as mock_run:
        docker_ship.plugin.pre_upload(docker_context)
    mock_run.assert_not_called()


def test_docker_ship_disabled(docker_context: CommandContext) -> None:
    docker_context.config.docker_ship.enabled = False
    with patch("subprocess.run") as mock_run:
        docker_ship.plugin.pre_upload(docker_context)
    mock_run.assert_not_called()


def test_docker_ship_missing_image(app_config: AppConfig) -> None:
    app_config.docker_ship = DockerShipConfig(enabled=True)
    ctx = CommandContext(
        command="upload",
        project_root=app_config.project_root,
        config=app_config,
        extras={"target": "docker"},
    )
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        pytest.raises(UploadError, match="Docker image name is required"),
    ):
        docker_ship.plugin.pre_upload(ctx)


def test_docker_ship_builds_image(docker_context: CommandContext) -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        docker_ship.plugin.pre_upload(docker_context)

    cmd = mock_run.call_args[0][0]
    assert cmd[:4] == ["/usr/bin/docker", "build", "-t", "myapp:v1"]


def test_docker_ship_no_docker_command(docker_context: CommandContext) -> None:
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(UploadError, match="docker command not found"),
    ):
        docker_ship.plugin.pre_upload(docker_context)


def test_docker_ship_pushes_when_configured(docker_context: CommandContext) -> None:
    docker_context.config.docker_ship.push = True
    with (
        patch("shutil.which", return_value="/usr/bin/docker"),
        patch("subprocess.run") as mock_run,
    ):
        docker_ship.plugin.post_upload(docker_context)

    cmd = mock_run.call_args[0][0]
    assert cmd == ["/usr/bin/docker", "push", "myapp:v1"]
