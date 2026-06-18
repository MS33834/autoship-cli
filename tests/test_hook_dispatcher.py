"""Tests for HookDispatcher."""

from __future__ import annotations

import pytest

from autoship.core.context import CommandContext
from autoship.core.hook_dispatcher import HookDispatcher
from autoship.hookspec import hookimpl
from autoship.models.config import AppConfig
from autoship.plugins import defaults


class PluginStub:
    def __init__(self) -> None:
        self.calls: list[str] = []

    @hookimpl
    def pre_init(self, context: CommandContext) -> None:
        self.calls.append("pre_init")

    @hookimpl
    def post_init(self, context: CommandContext) -> None:
        self.calls.append("post_init")


def test_builtin_plugins_loaded(app_config: AppConfig) -> None:
    dispatcher = HookDispatcher()
    assert dispatcher.pm.get_plugins()


def test_builtin_pre_commit_hook_is_registered(app_config: AppConfig) -> None:
    dispatcher = HookDispatcher()
    impls = dispatcher.pm.hook.pre_commit.get_hookimpls()
    assert any(isinstance(impl.plugin, defaults.BuiltinPlugins) for impl in impls)

    ctx = CommandContext(
        command="commit",
        project_root=app_config.project_root,
        config=app_config,
    )
    results = dispatcher.call("pre_commit", context=ctx, fail_fast=False)
    # Placeholder returns None, which pluggy filters out of the result list.
    assert results == []


def test_register_and_call_plugin(app_config: AppConfig) -> None:
    dispatcher = HookDispatcher()
    plugin = PluginStub()
    dispatcher.pm.register(plugin)

    ctx = CommandContext(
        command="init",
        project_root=app_config.project_root,
        config=app_config,
    )
    dispatcher.call("pre_init", context=ctx)
    dispatcher.call("post_init", context=ctx)

    assert plugin.calls == ["pre_init", "post_init"]


def test_call_returns_empty_list_when_no_hooks(app_config: AppConfig) -> None:
    dispatcher = HookDispatcher()
    ctx = CommandContext(
        command="verify",
        project_root=app_config.project_root,
        config=app_config,
    )
    results = dispatcher.call("pre_verify", context=ctx, fail_fast=False)
    assert results == []


def test_call_failing_hook_non_fail_fast_returns_empty(app_config: AppConfig) -> None:
    class BadPlugin:
        @hookimpl
        def pre_verify(self, context: CommandContext) -> None:
            raise RuntimeError("boom")

    dispatcher = HookDispatcher()
    dispatcher.pm.register(BadPlugin())
    ctx = CommandContext(
        command="verify",
        project_root=app_config.project_root,
        config=app_config,
    )
    results = dispatcher.call("pre_verify", context=ctx, fail_fast=False)
    assert results == []


def test_call_failing_hook_fail_fast_raises(app_config: AppConfig) -> None:
    from autoship.exceptions import PluginError

    class BadPlugin:
        @hookimpl
        def pre_verify(self, context: CommandContext) -> None:
            raise RuntimeError("boom")

    dispatcher = HookDispatcher()
    dispatcher.pm.register(BadPlugin())
    ctx = CommandContext(
        command="verify",
        project_root=app_config.project_root,
        config=app_config,
    )
    with pytest.raises(PluginError, match="Hook pre_verify failed"):
        dispatcher.call("pre_verify", context=ctx, fail_fast=True)
