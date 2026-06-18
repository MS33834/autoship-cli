"""Tests for default built-in plugins."""

from __future__ import annotations

from autoship.core.fix import FixSuggestion
from autoship.plugins.defaults import _parse_suggestion


def test_parse_suggestion_without_patch() -> None:
    text = "Increase the test timeout."
    suggestion = _parse_suggestion(text)
    assert suggestion == FixSuggestion(description="Increase the test timeout.")


def test_parse_suggestion_with_patch() -> None:
    text = (
        "Add the missing import.\n\n"
        "```diff\n"
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -1 +1 @@\n"
        "-print('hello')\n"
        "+import os\n"
        "```"
    )
    suggestion = _parse_suggestion(text)
    assert suggestion.description == "Add the missing import."
    assert "--- a/src/example.py" in suggestion.patch
    assert "```" not in suggestion.patch
