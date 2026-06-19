"""Example AutoShip-CLI plugin built with autoship-sdk.

This plugin demonstrates two common extension points:

- ``pre_commit``: run a lightweight check before ``autoship commit``.
- ``on_error``: return a fix suggestion when ``autoship verify --fix`` fails.
"""

from __future__ import annotations

from autoship_sdk import Plugin, hook

from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import VerifyError


class CustomPlugin(Plugin):
    """A sample plugin that warns about TODO files and suggests fixes."""

    @hook
    def pre_commit(self, context: CommandContext) -> None:
        """Warn if a TODO file exists in the project root."""
        todo_file = context.project_root / "TODO"
        if todo_file.exists():
            print(f"[custom-plugin] Warning: {todo_file} exists.")

    @hook
    def on_error(self, context: CommandContext, error: Exception) -> FixSuggestion | None:
        """Suggest a fix when a verification command fails and --fix is set."""
        if not context.extras.get("fix"):
            return None

        if isinstance(error, VerifyError):
            return FixSuggestion(
                description="[custom-plugin] Try running `autoship clean` and then re-run verify.",
            )

        return None


def register() -> CustomPlugin:
    """Factory used by the ``autoship.plugins`` entry point."""
    return CustomPlugin()
