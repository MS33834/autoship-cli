"""Tests for plugin hook dispatcher boundary behaviour."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from autoship.core.context import CommandContext
from autoship.core.hook_dispatcher import HookDispatcher
from autoship.core.plugin_registry import PluginRegistry, PluginSpec, TrustLevel
from autoship.core.sandbox import SandboxResult
from autoship.exceptions import PluginError
from autoship.hookspec import hookimpl
from autoship.models.config import AppConfig


@pytest.fixture
def dispatcher(tmp_path: Path) -> HookDispatcher:
    """Return a fresh HookDispatcher without entry-point discovery."""
    registry = PluginRegistry(registry_dir=tmp_path / "registry")
    with patch.object(HookDispatcher, "_discover_entry_points"):
        return HookDispatcher(registry=registry)


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


class CommunityPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> str:  # noqa: ARG002
        return f"community:{context.command}"


class _FakeSandboxRunner:
    def __init__(self, *, result: SandboxResult) -> None:
        self.result = result

    def run(self, command: list[str], **kwargs) -> SandboxResult:  # noqa: ARG002
        return self.result


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


def test_community_plugin_runs_in_sandbox(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="community_stub",
            source="community-stub",
            trust_level=TrustLevel.COMMUNITY,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="community_stub")

    dispatcher._sandbox_runner_factory = lambda **_: _FakeSandboxRunner(
        result=SandboxResult(returncode=0, stdout='{"result": "sandboxed"}', stderr="")
    )

    results = dispatcher.call("pre_commit", context=context)
    assert results == ["sandboxed"]


def test_verified_plugin_runs_directly(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="verified_stub",
            source="verified-stub",
            trust_level=TrustLevel.VERIFIED,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="verified_stub")

    results = dispatcher.call("pre_commit", context=context)
    assert results == ["community:test"]


def test_untrusted_plugin_runs_in_sandbox(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="untrusted_stub",
            source="untrusted-stub",
            trust_level=TrustLevel.UNTRUSTED,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="untrusted_stub")

    dispatcher._sandbox_runner_factory = lambda **_: _FakeSandboxRunner(
        result=SandboxResult(returncode=0, stdout='{"result": "sandboxed"}', stderr="")
    )

    results = dispatcher.call("pre_commit", context=context)
    assert results == ["sandboxed"]


def test_no_sandbox_option_runs_community_directly(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="community_stub",
            source="community-stub",
            trust_level=TrustLevel.COMMUNITY,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="community_stub")
    dispatcher._no_sandbox = True

    results = dispatcher.call("pre_commit", context=context)
    assert results == ["community:test"]


def test_sandbox_failure_respects_fail_fast(
    dispatcher: HookDispatcher, context: CommandContext
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="community_stub",
            source="community-stub",
            trust_level=TrustLevel.COMMUNITY,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="community_stub")

    dispatcher._sandbox_runner_factory = lambda **_: _FakeSandboxRunner(
        result=SandboxResult(returncode=1, stdout="", stderr="sandbox exploded")
    )

    with pytest.raises(PluginError, match="sandbox exploded"):
        dispatcher.call("pre_commit", context=context, fail_fast=True)


def test_sandbox_failure_non_fail_fast_returns_empty(
    dispatcher: HookDispatcher, context: CommandContext, caplog
) -> None:
    dispatcher.registry.add(
        PluginSpec(
            name="community_stub",
            source="community-stub",
            trust_level=TrustLevel.COMMUNITY,
        )
    )
    dispatcher.pm.register(CommunityPlugin(), name="community_stub")

    dispatcher._sandbox_runner_factory = lambda **_: _FakeSandboxRunner(
        result=SandboxResult(returncode=1, stdout="", stderr="sandbox exploded")
    )

    with caplog.at_level(logging.WARNING):
        results = dispatcher.call("pre_commit", context=context, fail_fast=False)
    assert results == []
    assert "sandbox exploded" in caplog.text
