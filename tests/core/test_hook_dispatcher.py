"""Tests for plugin hook dispatcher boundary behaviour."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from autoship.core.context import CommandContext
from autoship.core.hook_dispatcher import HookDispatcher
from autoship.exceptions import PluginError
from autoship.hookspec import hookimpl
from autoship.models.config import AppConfig


@pytest.fixture
def dispatcher() -> HookDispatcher:
    """Return a fresh HookDispatcher without entry-point discovery."""
    with patch.object(HookDispatcher, "_discover_entry_points"):
        return HookDispatcher()


@pytest.fixture
def context(project_root) -> CommandContext:
    return CommandContext(
        command="test",
        project_root=project_root,
        config=AppConfig(project_root=project_root),
    )


class FailingPlugin:
    @hookimpl
    def pre_clean(self, context: CommandContext) -> None:  # noqa: ARG002
        raise RuntimeError("boom")


class BadReturnPlugin:
    @hookimpl
    def pre_clean(self, context: CommandContext) -> str:  # noqa: ARG002
        return "unexpected"


def test_call_logs_and_raises_on_fail_fast(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.pm.register(FailingPlugin())
    with pytest.raises(PluginError, match="boom"):
        dispatcher.call("pre_clean", context=context, fail_fast=True)


def test_call_logs_and_continues_without_fail_fast(
    dispatcher: HookDispatcher, context: CommandContext, caplog
) -> None:
    dispatcher.pm.register(FailingPlugin())
    with caplog.at_level(logging.WARNING):
        results = dispatcher.call("pre_clean", context=context, fail_fast=False)
    assert results == []
    assert "pre_clean failed" in caplog.text


def test_call_returns_results(dispatcher: HookDispatcher, context: CommandContext) -> None:
    dispatcher.pm.register(BadReturnPlugin())
    results = dispatcher.call("pre_clean", context=context)
    assert results == ["unexpected"]


def test_entry_point_load_failure_is_logged(caplog) -> None:
    fake_ep = MagicMock()
    fake_ep.name = "broken"
    fake_ep.load.side_effect = ImportError("no module")

    with (
        patch.object(HookDispatcher, "_load_builtin"),
        patch("autoship.core.hook_dispatcher.entry_points") as mock_eps,
    ):
        mock_eps.return_value.select.return_value = [fake_ep]
        HookDispatcher()

    assert "Failed to load plugin broken" in caplog.text
