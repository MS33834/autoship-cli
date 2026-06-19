"""Tests for the LLM fix command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autoship.cli.commands import fix as fix_module
from autoship.cli.main import app

runner = CliRunner()


def test_fix_requires_api_key(tmp_path: Path) -> None:
    error_log = tmp_path / "error.txt"
    error_log.write_text("SyntaxError", encoding="utf-8")
    with patch.dict("os.environ", {"AUTOSHIP_LLM__API_KEY": ""}, clear=False):
        result = runner.invoke(app, ["fix", str(error_log)])
    assert result.exit_code != 0
    assert "API key" in result.output


def test_fix_requires_error_log(tmp_path: Path) -> None:
    missing_log = tmp_path / "missing.txt"
    result = runner.invoke(app, ["fix", str(missing_log)])
    assert result.exit_code != 0
    assert "No error log" in result.output


def test_fix_empty_error_log(tmp_path: Path) -> None:
    empty_log = tmp_path / "empty.txt"
    empty_log.write_text("   ", encoding="utf-8")
    result = runner.invoke(app, ["fix", str(empty_log)])
    assert result.exit_code != 0
    assert "empty" in result.output


def test_fix_calls_llm_and_shows_suggestion(tmp_path: Path) -> None:
    error_log = tmp_path / "error.txt"
    error_log.write_text("NameError: name 'x' is not defined", encoding="utf-8")

    with (
        patch.dict("os.environ", {"AUTOSHIP_LLM__API_KEY": "fake-key"}, clear=False),
        patch("autoship.cli.commands.fix.LlmClient") as mock_client,
    ):
        mock_client.return_value.chat.return_value = "Add `x = 0` before usage."
        result = runner.invoke(app, ["fix", str(error_log)])

    assert result.exit_code == 0
    assert "Add `x = 0`" in result.output


def test_fix_yes_flag_applies_patch(tmp_path: Path) -> None:
    error_log = tmp_path / "error.txt"
    error_log.write_text("error", encoding="utf-8")

    patch_text = "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"

    with (
        patch.dict("os.environ", {"AUTOSHIP_LLM__API_KEY": "fake-key"}, clear=False),
        patch("autoship.cli.commands.fix.LlmClient") as mock_client,
        patch("autoship.cli.commands.fix._apply_patch") as mock_apply,
    ):
        mock_client.return_value.chat.return_value = f"```diff\n{patch_text}\n```"
        result = runner.invoke(app, ["fix", str(error_log), "--yes"])

    assert result.exit_code == 0
    mock_apply.assert_called_once()


def test_extract_patch_from_diff_block() -> None:
    response = "```diff\n--- a\n+++ b\n```"
    assert fix_module._extract_patch(response) == "--- a\n+++ b"


def test_extract_patch_from_plain_diff() -> None:
    response = "Some text\n--- a/file.txt\n+++ b/file.txt"
    assert fix_module._extract_patch(response) == "--- a/file.txt\n+++ b/file.txt"


def test_extract_patch_returns_none_when_no_patch() -> None:
    assert fix_module._extract_patch("No patch here") is None


def test_collect_relevant_files(tmp_path: Path) -> None:
    py_file = tmp_path / "module.py"
    py_file.write_text("x = 1", encoding="utf-8")
    error_context = f"Error in {py_file}"
    files = fix_module._collect_relevant_files(tmp_path, error_context)
    assert "module.py" in files


def test_apply_patch_with_git(tmp_path: Path) -> None:
    patch_text = "diff content"
    i18n_mock = MagicMock()
    i18n_mock._ = MagicMock(return_value="ok")

    check = MagicMock(returncode=0)
    apply = MagicMock(returncode=0)

    with (
        patch("shutil.which", side_effect=["git", None]),
        patch("subprocess.run", side_effect=[check, apply]) as mock_run,
    ):
        fix_module._apply_patch(tmp_path, patch_text, i18n_mock)

    assert mock_run.call_count == 2
    assert mock_run.call_args_list[0][0][0] == ["git", "apply", "--check"]


def test_apply_patch_with_patch_command(tmp_path: Path) -> None:
    patch_text = "diff content"
    i18n_mock = MagicMock()
    i18n_mock._ = MagicMock(return_value="ok")

    proc = MagicMock(returncode=0)

    with (
        patch("shutil.which", side_effect=[None, "patch"]),
        patch("subprocess.run", return_value=proc) as mock_run,
    ):
        fix_module._apply_patch(tmp_path, patch_text, i18n_mock)

    assert mock_run.call_args[0][0] == ["patch", "-p1"]


def test_apply_patch_no_tool(tmp_path: Path) -> None:
    patch_text = "diff content"
    i18n_mock = MagicMock()
    i18n_mock._ = MagicMock(return_value="no tool")

    with patch("shutil.which", return_value=None):
        fix_module._apply_patch(tmp_path, patch_text, i18n_mock)


def test_patch_paths_are_safe_accepts_relative_paths(tmp_path: Path) -> None:
    patch = "--- a/src/foo.py\n+++ b/src/foo.py\n@@ -1 +1 @@\n-old\n+new"
    assert fix_module._patch_paths_are_safe(tmp_path, patch) is True


def test_patch_paths_are_safe_rejects_absolute_paths(tmp_path: Path) -> None:
    patch = "--- /etc/passwd\n+++ /etc/passwd\n@@ -1 +1 @@\n-old\n+new"
    assert fix_module._patch_paths_are_safe(tmp_path, patch) is False


def test_patch_paths_are_safe_rejects_traversal(tmp_path: Path) -> None:
    patch = "--- a/../etc/passwd\n+++ b/../etc/passwd\n@@ -1 +1 @@\n-old\n+new"
    assert fix_module._patch_paths_are_safe(tmp_path, patch) is False
