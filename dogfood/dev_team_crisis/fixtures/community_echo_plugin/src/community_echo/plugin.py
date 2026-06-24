"""Minimal community plugin for D3 conflict tests."""

from __future__ import annotations

from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class CommunityEchoPlugin:
    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        context.extras["community_echo_ran"] = True


def register() -> CommunityEchoPlugin:
    return CommunityEchoPlugin()
