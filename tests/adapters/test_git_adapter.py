"""Tests for GitAdapter."""

from __future__ import annotations

import subprocess

import pytest

from autoship.adapters.git_adapter import GitAdapter


@pytest.fixture
def git_repo(project_root) -> GitAdapter:
    subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    return GitAdapter(project_root)


def test_has_changes_false_for_clean_repo(git_repo: GitAdapter, project_root) -> None:
    assert git_repo.has_changes() is False


def test_has_changes_true_for_untracked(git_repo: GitAdapter, project_root) -> None:
    (project_root / "file.txt").write_text("hello", encoding="utf-8")
    assert git_repo.has_changes() is True


def test_diff_and_stats_empty_for_clean_repo(git_repo: GitAdapter) -> None:
    assert git_repo.diff() == ""
    assert git_repo.stats() == ""


def test_commit_stages_and_commits(git_repo: GitAdapter, project_root) -> None:
    (project_root / "file.txt").write_text("hello", encoding="utf-8")
    git_repo.commit("Initial commit")
    assert git_repo.has_changes() is False
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Initial commit" in result.stdout
