"""Tests for the PyPI upload adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from autoship.adapters.upload.pypi import PyPIUploader
from autoship.exceptions import UploadError


def test_pypi_dry_run(project_root: Path) -> None:
    uploader = PyPIUploader(project_root, repository="testpypi")
    result = uploader.upload(dry_run=True)
    assert result.success is True
    assert result.target == "pypi"
    assert result.details["repository"] == "testpypi"


def test_pypi_validate_missing_tools(project_root: Path) -> None:
    uploader = PyPIUploader(project_root)
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(UploadError, match="Required tool"),
    ):
        uploader.validate()


def test_pypi_upload_success(project_root: Path) -> None:
    uploader = PyPIUploader(project_root, repository="pypi")
    with (
        patch("shutil.which", return_value="/usr/bin/twine"),
        patch("subprocess.run") as mock_run,
    ):
        result = uploader.upload()
    assert result.success is True
    assert result.details["repository"] == "pypi"
    assert mock_run.call_count == 2
