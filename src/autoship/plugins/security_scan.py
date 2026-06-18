"""Official security-scan plugin for AutoShip-CLI.

Runs lightweight security checks during the ``pre_commit`` hook. Tools are
invoked only when present on PATH, so the plugin degrades gracefully on
systems where ``bandit``, ``gitleaks`` or ``osv-scanner`` are not installed.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Any

from autoship.core.context import CommandContext
from autoship.exceptions import SecurityScanError
from autoship.hookspec import hookimpl
from autoship.models.config import SecurityThreshold

logger = logging.getLogger("autoship")

_SEVERITY_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


class SecurityScanPlugin:
    """Built-in security scanner invoked before each commit."""

    @hookimpl
    def pre_commit(self, context: CommandContext) -> None:
        """Run configured security scanners and abort if issues exceed threshold."""
        config = context.config.security
        if not config.enabled:
            return

        findings: list[dict[str, Any]] = []
        for tool in config.tools:
            tool_findings = _run_scanner(tool, context.project_root, config.threshold)
            findings.extend(tool_findings)

        summary = _summarize(findings)
        logger.info(
            "Security scan completed: %s findings (%s high, %s medium, %s low)",
            summary["total"],
            summary["high"],
            summary["medium"],
            summary["low"],
        )

        if summary["max_severity_value"] >= _SEVERITY_ORDER[config.threshold.value.upper()]:
            message = (
                f"Security scan found {summary['total']} issue(s) "
                f"at or above '{config.threshold.value}' threshold."
            )
            raise SecurityScanError(
                message,
                details={"findings": findings, "summary": summary},
            )


def _run_scanner(
    tool: str, project_root: Any, threshold: SecurityThreshold
) -> list[dict[str, Any]]:
    """Dispatch to the requested scanner if it is available on PATH."""
    executable = shutil.which(tool)
    if executable is None:
        logger.warning("Security scanner %r not found on PATH; skipping.", tool)
        return []

    if tool == "bandit":
        return _scan_bandit(executable, project_root, threshold)
    if tool == "gitleaks":
        return _scan_gitleaks(executable, project_root)
    if tool == "osv-scanner":
        return _scan_osv(executable, project_root)

    logger.warning("Unsupported security scanner %r; skipping.", tool)
    return []


def _scan_bandit(
    executable: str, project_root: Any, threshold: SecurityThreshold
) -> list[dict[str, Any]]:
    """Run bandit and return normalized findings."""
    level_flag = {
        SecurityThreshold.LOW: "-l",
        SecurityThreshold.MEDIUM: "-ll",
        SecurityThreshold.HIGH: "-lll",
    }[threshold]

    result = subprocess.run(
        [executable, "-r", "-f", "json", level_flag, "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    findings: list[dict[str, Any]] = []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return findings

    for issue in data.get("results", []):
        findings.append(
            {
                "tool": "bandit",
                "severity": issue.get("issue_severity", "LOW"),
                "confidence": issue.get("issue_confidence", "UNDEFINED"),
                "summary": issue.get("issue_text", ""),
                "filename": issue.get("filename"),
                "line": issue.get("line_number"),
            }
        )
    return findings


def _scan_gitleaks(executable: str, project_root: Any) -> list[dict[str, Any]]:
    """Run gitleaks and return normalized findings."""
    result = subprocess.run(
        [executable, "detect", "--source", ".", "--no-banner", "--verbose"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return []

    return [
        {
            "tool": "gitleaks",
            "severity": "HIGH",
            "summary": "Potential secret detected by gitleaks",
            "details": result.stdout or result.stderr,
        }
    ]


def _scan_osv(executable: str, project_root: Any) -> list[dict[str, Any]]:
    """Run osv-scanner and return normalized findings."""
    result = subprocess.run(
        [executable, "--format", "json", "-r", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    findings: list[dict[str, Any]] = []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return findings

    for entry in data.get("results", []):
        for pkg in entry.get("packages", []):
            for vuln in pkg.get("vulnerabilities", []):
                findings.append(
                    {
                        "tool": "osv-scanner",
                        "severity": _osv_severity(vuln),
                        "summary": vuln.get("summary", "OSV vulnerability"),
                        "id": vuln.get("id"),
                    }
                )
    return findings


def _osv_severity(vuln: dict[str, Any]) -> str:
    """Extract the highest CVSS severity from an OSV vulnerability record."""
    severities = vuln.get("severity", [])
    if not severities:
        return "MEDIUM"
    order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    highest = max(
        (order.get(s.get("type", "").upper() or s.get("score", "").upper(), 0) for s in severities),
        default=2,
    )
    for label, value in order.items():
        if value == highest:
            return label
    return "MEDIUM"


def _summarize(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate findings into a simple severity summary."""
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for finding in findings:
        severity = finding.get("severity", "LOW").upper()
        counts[severity] = counts.get(severity, 0) + 1

    max_value = max(
        (_SEVERITY_ORDER.get(severity, 0) for severity in counts if counts[severity] > 0),
        default=0,
    )
    max_severity = next(
        (label for label, value in _SEVERITY_ORDER.items() if value == max_value),
        "LOW",
    )

    return {
        "total": len(findings),
        "low": counts["LOW"],
        "medium": counts["MEDIUM"],
        "high": counts["HIGH"],
        "max_severity": max_severity,
        "max_severity_value": max_value,
    }


plugin = SecurityScanPlugin()
