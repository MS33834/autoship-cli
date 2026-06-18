"""Tests for the built-in security-scan plugin."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from autoship.core.context import CommandContext
from autoship.exceptions import SecurityScanError
from autoship.models.config import AppConfig, SecurityThreshold
from autoship.plugins import security_scan


@pytest.fixture
def security_context(app_config: AppConfig) -> CommandContext:
    """Return a CommandContext with security scanning enabled."""
    return CommandContext(
        command="commit",
        project_root=app_config.project_root,
        config=app_config,
    )


def _bandit_json(severity: str) -> str:
    return f'{{"results": [{{"issue_severity": "{severity}", "issue_confidence": "HIGH", "issue_text": "bad", "filename": "x.py", "line_number": 1}}]}}'


def test_security_scan_disabled(security_context: CommandContext) -> None:
    security_context.config.security.enabled = False
    with patch("subprocess.run") as mock_run:
        security_scan.plugin.pre_commit(security_context)
    mock_run.assert_not_called()


def test_security_scan_skips_missing_tool(security_context: CommandContext) -> None:
    with (
        patch("shutil.which", return_value=None),
        patch("subprocess.run") as mock_run,
    ):
        security_scan.plugin.pre_commit(security_context)
    mock_run.assert_not_called()


def test_bandit_high_triggers_error(security_context: CommandContext) -> None:
    with (
        patch("shutil.which", return_value="/usr/bin/bandit"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.stdout = _bandit_json("HIGH")
        with pytest.raises(SecurityScanError, match="Security scan found"):
            security_scan.plugin.pre_commit(security_context)


def test_bandit_low_below_high_threshold(security_context: CommandContext) -> None:
    security_context.config.security.threshold = SecurityThreshold.HIGH
    with (
        patch("shutil.which", return_value="/usr/bin/bandit"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.stdout = _bandit_json("LOW")
        security_scan.plugin.pre_commit(security_context)


def test_gitleaks_detects_secret(security_context: CommandContext) -> None:
    security_context.config.security.tools = ["gitleaks"]
    with (
        patch("shutil.which", return_value="/usr/bin/gitleaks"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "leak"
        mock_run.return_value.stderr = ""
        with pytest.raises(SecurityScanError, match="Security scan found"):
            security_scan.plugin.pre_commit(security_context)


def test_osv_scanner_detects_vulnerability(security_context: CommandContext) -> None:
    security_context.config.security.tools = ["osv-scanner"]
    payload = (
        '{"results": [{"packages": [{"vulnerabilities": ['
        '{"id": "GHSA-1", "summary": "bad lib", "severity": [{"type": "CVSS_V3", "score": "HIGH"}]}'
        "]}]}]}"
    )
    with (
        patch("shutil.which", return_value="/usr/bin/osv-scanner"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value.stdout = payload
        with pytest.raises(SecurityScanError, match="Security scan found"):
            security_scan.plugin.pre_commit(security_context)


def test_unsupported_tool_is_skipped(security_context: CommandContext) -> None:
    security_context.config.security.tools = ["unknown-tool"]
    with patch("shutil.which", return_value="/usr/bin/unknown-tool"):
        security_scan.plugin.pre_commit(security_context)


def test_summarize_empty() -> None:
    assert security_scan._summarize([]) == {
        "total": 0,
        "low": 0,
        "medium": 0,
        "high": 0,
        "max_severity": "LOW",
        "max_severity_value": 0,
    }


def test_summarize_multiple() -> None:
    findings = [
        {"severity": "LOW"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
    ]
    summary = security_scan._summarize(findings)
    assert summary["total"] == 3
    assert summary["max_severity"] == "HIGH"
    assert summary["max_severity_value"] == 3
