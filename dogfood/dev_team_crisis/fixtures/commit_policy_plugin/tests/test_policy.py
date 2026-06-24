"""Tests for autoship-commit-policy."""

from __future__ import annotations

from pathlib import Path

import pytest
from commit_policy.plugin import CommitPolicyPlugin

from autoship.core.context import CommandContext
from autoship.exceptions import VerifyError
from autoship.models.config import AppConfig


def _context(message: str) -> CommandContext:
    return CommandContext(
        command="commit",
        project_root=Path("."),
        config=AppConfig(),
        extras={"message": message},
    )


def test_valid_message_passes() -> None:
    plugin = CommitPolicyPlugin()
    plugin.pre_commit(_context("feat(core): add policy"))


def test_invalid_format_raises() -> None:
    plugin = CommitPolicyPlugin()
    with pytest.raises(VerifyError):
        plugin.pre_commit(_context("add policy"))


def test_wip_message_blocked_when_enabled() -> None:
    plugin = CommitPolicyPlugin(block_wip=True)
    with pytest.raises(VerifyError):
        plugin.pre_commit(_context("feat(core): WIP add policy"))


def test_wip_message_allowed_when_disabled() -> None:
    plugin = CommitPolicyPlugin(block_wip=False)
    plugin.pre_commit(_context("feat(core): WIP add policy"))


def test_i18n_message() -> None:
    plugin = CommitPolicyPlugin(locale="zh")
    ctx = _context("bad message")
    with pytest.raises(VerifyError) as exc_info:
        plugin.pre_commit(ctx)
    assert "不符合" in str(exc_info.value)
