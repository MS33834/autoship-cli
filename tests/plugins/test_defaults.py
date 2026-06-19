"""Tests for default built-in plugins."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import SecurityScanError
from autoship.plugins.defaults import _parse_suggestion, plugin


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


def test_parse_suggestion_with_backticks_inside_patch() -> None:
    text = (
        "Fix the markdown string.\n\n"
        "```diff\n"
        "--- a/src/example.py\n"
        "+++ b/src/example.py\n"
        "@@ -1 +1 @@\n"
        "-x = 'hello ```world```'\n"
        "+x = 'hello world'\n"
        "```"
    )
    suggestion = _parse_suggestion(text)
    assert suggestion.description == "Fix the markdown string."
    assert "```world```" in suggestion.patch
    assert suggestion.patch.endswith("+x = 'hello world'")


def test_parse_suggestion_with_multiple_patches() -> None:
    text = (
        "Update both files.\n\n"
        "```diff\n"
        "--- a/src/one.py\n"
        "+++ b/src/one.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
        "```\n\n"
        "```diff\n"
        "--- a/src/two.py\n"
        "+++ b/src/two.py\n"
        "@@ -1 +1 @@\n"
        "-foo\n"
        "+bar\n"
        "```"
    )
    suggestion = _parse_suggestion(text)
    assert suggestion.description == "Update both files."
    assert "--- a/src/one.py" in suggestion.patch
    assert "--- a/src/two.py" in suggestion.patch
    assert "+new" in suggestion.patch
    assert "+bar" in suggestion.patch
    assert "```" not in suggestion.patch


def test_pre_commit_delegates_to_security_scan(command_context: CommandContext) -> None:
    """Builtin pre_commit should forward to the real security-scan plugin."""
    with patch("autoship.plugins.security_scan.plugin.pre_commit") as mock_pre_commit:
        plugin.pre_commit(command_context)
    mock_pre_commit.assert_called_once_with(command_context)


def test_pre_commit_propagates_security_scan_error(command_context: CommandContext) -> None:
    """Exceptions raised by the security-scan plugin should bubble up."""
    with (
        patch(
            "autoship.plugins.security_scan.plugin.pre_commit",
            side_effect=SecurityScanError("scan failed"),
        ),
        pytest.raises(SecurityScanError, match="scan failed"),
    ):
        plugin.pre_commit(command_context)
