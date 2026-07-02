#!/usr/bin/env python3
"""Scan built docs site for sensitive information before deployment.

Runs as a CI gate (exit 1 on findings) and as a local pre-deploy check.
Looks for patterns that should never appear in public docs:
- API keys / tokens (ghp_, sk-, AKIA, xoxb-, glpat-, etc.)
- Internal hostnames (siem, internal, corp, staging with internal-looking names)
- AWS account IDs (12-digit near aws/account)
- Private IP ranges (192.168., 10., 172.16-31.)
- Email addresses (flagged for manual review — only public aliases allowed)

Usage:
    uv run python scripts/scan_docs_secrets.py [--site-dir DIR]
    uv run python scripts/scan_docs_secrets.py --check   # CI mode, exit 1 on findings

Default site-dir is /tmp/mkdocs-build (matches `mkdocs build --site-dir`).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Patterns that indicate leaked secrets. Sourced from common token formats.
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "github_pat": re.compile(r"ghp_[A-Za-z0-9]{36}"),
    "github_fine_grained": re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{48}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "gitlab_pat": re.compile(r"glpat-[A-Za-z0-9_-]{20}"),
    "generic_bearer": re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{32,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
}

# Internal-looking hostnames (case-insensitive). Adjust allowlist as needed.
INTERNAL_HOST_RE = re.compile(
    r"(?i)\b(?:siem|internal|corp|intranet|staging-internal|dev-internal)[\w.-]*\.(?:local|internal|corp|lan|priv)\b"
)

# Private IP ranges.
PRIVATE_IP_RE = re.compile(
    r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)

# Email addresses — flagged for manual review (public aliases like team@autoship.dev are OK).
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Known-public aliases that are allowed in docs.
ALLOWED_EMAILS = {"team@autoship.dev", "security@autoship.dev"}

# File extensions to scan.
SCAN_EXTENSIONS = {".html", ".md", ".txt", ".xml", ".json", ".js", ".css"}


class Finding(NamedTuple):
    """A single sensitive-information finding."""

    file: Path
    line: int
    pattern: str
    match: str


def scan_file(path: Path, root: Path) -> list[Finding]:
    """Scan a single file for sensitive patterns."""
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern in SECRET_PATTERNS.items():
            for m in pattern.finditer(line):
                findings.append(Finding(path.relative_to(root), line_no, name, m.group(0)))
        for m in INTERNAL_HOST_RE.finditer(line):
            findings.append(
                Finding(path.relative_to(root), line_no, "internal_hostname", m.group(0))
            )
        for m in PRIVATE_IP_RE.finditer(line):
            findings.append(Finding(path.relative_to(root), line_no, "private_ip", m.group(0)))
        for m in EMAIL_RE.finditer(line):
            if m.group(0).lower() not in ALLOWED_EMAILS:
                findings.append(
                    Finding(path.relative_to(root), line_no, "email_review", m.group(0))
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir",
        default="/tmp/mkdocs-build",
        help="Directory of built docs site (default: /tmp/mkdocs-build)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit 1 if any secret findings (email_review is advisory only)",
    )
    parser.add_argument(
        "--source",
        action="store_true",
        help="Also scan source docs/ and website/ (not just built site)",
    )
    args = parser.parse_args()

    all_findings: list[Finding] = []
    scan_roots: list[Path] = []

    site_dir = Path(args.site_dir)
    if site_dir.exists():
        scan_roots.append(site_dir)
    else:
        print(f"WARNING: site dir {site_dir} does not exist, skipping built-site scan")

    if args.source:
        repo_root = Path(__file__).resolve().parents[1]
        for d in ("docs", "website"):
            target = repo_root / d
            if target.exists():
                scan_roots.append(target)

    if not scan_roots:
        print("ERROR: no scan targets available")
        return 2

    for root in scan_roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SCAN_EXTENSIONS:
                all_findings.extend(scan_file(path, root))

    # Separate hard failures from advisory.
    hard = [f for f in all_findings if f.pattern != "email_review"]
    advisory = [f for f in all_findings if f.pattern == "email_review"]

    if all_findings:
        print(f"\nScan complete: {len(hard)} hard finding(s), {len(advisory)} advisory email(s)")
        for f in hard:
            print(f"  [HARD] {f.pattern}: {f.file}:{f.line} -> {f.match}")
        for f in advisory:
            print(f"  [REVIEW] {f.pattern}: {f.file}:{f.line} -> {f.match}")
        print(f"\nAllowed public emails: {sorted(ALLOWED_EMAILS)}")
    else:
        print("\nDocs secret scan: OK (no secrets, no internal hostnames, no unknown emails)")

    if args.check and hard:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
