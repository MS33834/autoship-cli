"""Tests for the GitHub release upload adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoship.adapters.upload.github import GitHubUploader
from autoship.exceptions import UploadError


def test_github_dry_run(project_root: Path) -> None:
    uploader = GitHubUploader(project_root, tag="v1.0.0")
    result = uploader.upload(dry_run=True)
    assert result.success is True
    assert result.target == "github"
    assert result.details["dry_run"] is True


def test_github_validate_missing_cli(project_root: Path) -> None:
    uploader = GitHubUploader(project_root, tag="v1.0.0")
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(UploadError, match="gh` CLI not found"),
    ):
        uploader.validate()


def test_github_upload_success(project_root: Path) -> None:
    uploader = GitHubUploader(project_root, tag="v1.0.0", artifacts=["dist/*"])
    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run") as mock_run,
    ):
        result = uploader.upload()
    assert result.success is True
    assert result.url == "https://github.com/release/v1.0.0"
    assert mock_run.call_count == 2
