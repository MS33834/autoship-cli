"""Default built-in plugin implementations."""

from __future__ import annotations

from autoship.core.context import CommandContext
from autoship.hookspec import hookimpl


class BuiltinPlugins:
    """Placeholder built-in plugins; real security scans will live here."""

    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        """Placeholder: will eventually run gitleaks / bandit checks."""


plugin = BuiltinPlugins()
