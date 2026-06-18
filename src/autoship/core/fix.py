"""Fix suggestion data model for ``on_error`` hooks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FixSuggestion:
    """A suggested fix returned by an ``on_error`` hook.

    Attributes:
        description: Human-readable explanation of the fix.
        patch: Optional unified diff that can be applied to the project.
    """

    description: str
    patch: str | None = None
