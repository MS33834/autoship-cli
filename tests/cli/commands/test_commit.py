"""Tests for the commit command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from autoship.cli.commands import commit
from autoship.exceptions import GitError, ModelGatewayError
from autoship.models.config import AppConfig


def test_commit_no_changes(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with patch.object(commit.GitAdapter, "has_changes", return_value=False):
        result = commit.commit(ctx)
    assert result is None


def test_commit_with_message_dry_run(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": True,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(commit.GitAdapter, "has_changes", return_value=True),
        patch.object(commit.GitAdapter, "diff", return_value="diff"),
        patch.object(commit.GitAdapter, "stats", return_value="stats"),
    ):
        commit.commit(ctx, message="fix: bug")


def test_commit_generates_message_and_commits(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(commit.GitAdapter, "has_changes", return_value=True),
        patch.object(commit.GitAdapter, "diff", return_value="diff"),
        patch.object(commit.GitAdapter, "stats", return_value="stats"),
        patch.object(
            commit.ModelRouter, "generate_commit_message", return_value="feat: add feature"
        ),
        patch.object(commit.GitAdapter, "commit") as mock_commit,
    ):
        commit.commit(ctx, message=None)
    mock_commit.assert_called_once_with("feat: add feature")


def test_commit_model_failure_fallback(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(commit.GitAdapter, "has_changes", return_value=True),
        patch.object(commit.GitAdapter, "diff", return_value="diff"),
        patch.object(commit.GitAdapter, "stats", return_value="stats"),
        patch.object(
            commit.ModelRouter, "generate_commit_message", side_effect=ModelGatewayError("down")
        ),
        patch.object(commit.GitAdapter, "commit") as mock_commit,
    ):
        commit.commit(ctx, message=None)
    mock_commit.assert_called_once_with("Update files")


def test_commit_git_error_raises(project_root, app_config: AppConfig) -> None:
    ctx = MagicMock()
    ctx.obj = {
        "config": app_config,
        "audit_logger": MagicMock(),
        "dry_run": False,
        "yes": True,
        "verbose": False,
    }
    with (
        patch.object(commit.GitAdapter, "has_changes", return_value=True),
        patch.object(commit.GitAdapter, "diff", return_value="diff"),
        patch.object(commit.GitAdapter, "stats", return_value="stats"),
        patch.object(commit.ModelRouter, "generate_commit_message", return_value="feat: update"),
        patch.object(commit.GitAdapter, "commit", side_effect=GitError("boom")),
        pytest.raises(GitError),
    ):
        commit.commit(ctx, message=None)
