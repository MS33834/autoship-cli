#!/usr/bin/env python3
"""Generate a Keep a Changelog entry for a release and insert it into CHANGELOG.md.

Used by the Release workflow (``.github/workflows/release.yml``) to automatically
update the root ``CHANGELOG.md`` from the GitHub Release notes. The script is
intentionally dependency-free (stdlib only) so it can run in CI without a full
environment sync, and idempotent so re-runs never duplicate an entry.

Usage::

    python scripts/release_changelog.py \
        --version 1.1.0 --date 2026-07-02 \
        --notes-file notes.md --changelog CHANGELOG.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import sys

# Matches Keep a Changelog version headings, e.g. ``## [1.2.3]`` or ``## [Unreleased]``.
VERSION_HEADING_RE = re.compile(r"^##\s*\[(.+?)\]")
UNRELEASED = "Unreleased"


def render_entry(version: str, date: str, body: str) -> str:
    """Render a ``## [version] - date`` Keep a Changelog section."""
    header = f"## [{version}] - {date}" if date else f"## [{version}]"
    cleaned = _clean_body(body).strip()
    parts = [header, ""]
    if cleaned:
        parts.append(cleaned)
        parts.append("")
    return "\n".join(parts)


def _clean_body(body: str) -> str:
    """Drop GitHub-generated footer noise we don't want in CHANGELOG.md."""
    keep: list[str] = []
    skip_compare_url = False
    for line in body.splitlines():
        if line.strip().startswith("## Full Changelog"):
            skip_compare_url = True
            continue
        if skip_compare_url:
            # The heading is followed by a single compare URL line; skip it, then resume.
            skip_compare_url = False
            if line.strip().startswith("https://"):
                continue
            if not line.strip():
                continue
        keep.append(line)
    return "\n".join(keep)


def find_version(content: str, version: str) -> bool:
    """Return True if a section for ``version`` already exists."""
    for line in content.splitlines():
        match = VERSION_HEADING_RE.match(line)
        if match and match.group(1) == version:
            return True
    return False


def _section_end(lines: list[str], start: int) -> int:
    """Return the index of the next ``## [`` heading after ``start``, or len(lines)."""
    for j in range(start + 1, len(lines)):
        if VERSION_HEADING_RE.match(lines[j]):
            return j
    return len(lines)


def insert_entry(content: str, entry: str, version: str) -> str:
    """Insert ``entry`` for ``version`` preserving the Unreleased section and order.

    A released version is placed after ``## [Unreleased]`` (if present) and before
    the most recent released version, matching Keep a Changelog conventions.
    """
    del version  # the entry already carries the heading; kept for a stable API
    lines = content.splitlines()
    headings: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        match = VERSION_HEADING_RE.match(line)
        if match:
            headings.append((i, match.group(1)))
    released = [(i, name) for i, name in headings if name != UNRELEASED]
    has_unreleased = any(name == UNRELEASED for _, name in headings)

    if released:
        insert_at = released[0][0]
    elif has_unreleased:
        unreleased_idx = next(i for i, name in headings if name == UNRELEASED)
        insert_at = _section_end(lines, unreleased_idx)
    else:
        insert_at = len(lines)
        for i, line in enumerate(lines):
            if re.match(r"^##\s+", line):
                insert_at = i
                break

    block = entry.rstrip("\n").split("\n")
    new_lines = lines[:insert_at]
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")
    new_lines.extend(block)
    new_lines.append("")
    new_lines.extend(lines[insert_at:])
    result = "\n".join(new_lines)
    return result if result.endswith("\n") else result + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.1.0")
    parser.add_argument(
        "--date",
        default=None,
        help="release date as YYYY-MM-DD; defaults to today (UTC) when omitted",
    )
    parser.add_argument(
        "--notes-file",
        default=None,
        help="path to the release notes body; reads stdin when omitted",
    )
    parser.add_argument("--changelog", default="CHANGELOG.md", help="path to CHANGELOG.md")
    parser.add_argument("--dry-run", action="store_true", help="print the result without writing")
    args = parser.parse_args(argv)

    if not re.fullmatch(r"[0-9A-Za-z.+-]+", args.version):
        print(f"error: invalid version '{args.version}'", file=sys.stderr)
        return 2

    date = args.date or dt.date.today().isoformat()
    body = (
        pathlib.Path(args.notes_file).read_text(encoding="utf-8")
        if args.notes_file
        else sys.stdin.read()
    )
    path = pathlib.Path(args.changelog)
    content = path.read_text(encoding="utf-8") if path.exists() else ""

    if find_version(content, args.version):
        print(f"CHANGELOG.md already contains [{args.version}]; nothing to do.")
        return 0

    entry = render_entry(args.version, date, body)
    new_content = insert_entry(content, entry, args.version)

    if args.dry_run:
        sys.stdout.write(new_content)
        return 0

    path.write_text(new_content, encoding="utf-8")
    print(f"CHANGELOG.md updated with [{args.version}] - {date}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
