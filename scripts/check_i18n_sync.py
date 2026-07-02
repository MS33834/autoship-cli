#!/usr/bin/env python3
"""Check i18n sync between zh docs (default locale) and en/ja translations.

Compares structural elements of Markdown files under ``docs/`` (zh, the
default locale) against the matching files under ``docs/en/`` and ``docs/ja/``:

* H2/H3 heading counts (lines starting with ``## `` / ``### ``)
* fenced code block counts (pairs of ````` `` fences)
* YAML front-matter keys (keys present in zh must be present in translations)

Mapping rules:
* ``docs/<name>.md``          ↔ ``docs/{en,ja}/<name>.md``
* ``docs/commands/<name>.md`` ↔ ``docs/{en,ja}/commands/<name>.md``

Exit codes:
* 0 — all checked files are structurally consistent (warnings allowed)
* 1 — at least one ERROR (heading/code-block count or front-matter mismatch)

Stdlib only. Used by the CI ``docs`` job.
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass, field

H2_RE = re.compile(r"^##\s+")
H3_RE = re.compile(r"^###\s+")
FENCE_RE = re.compile(r"^```")
# mkdocs snippet include directive, e.g. ``--8<-- "CONTRIBUTING.md"``.
SNIPPET_RE = re.compile(r"--8<--")
FRONT_MATTER_DELIM = "---"
LANGS: tuple[str, ...] = ("en", "ja")


@dataclass
class DocStats:
    """Structural statistics for a single Markdown file."""

    h2_count: int = 0
    h3_count: int = 0
    code_blocks: int = 0
    front_matter_keys: set[str] = field(default_factory=lambda: set[str]())
    has_snippet: bool = False


def parse_front_matter(lines: list[str]) -> set[str]:
    """Return top-level keys from YAML front matter (between ``---`` fences).

    Returns an empty set when the file has no front matter.
    """
    if len(lines) < 2 or lines[0].strip() != FRONT_MATTER_DELIM:
        return set()
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == FRONT_MATTER_DELIM:
            break
        # Only top-level "key: value" lines (no leading whitespace, has a colon).
        if line and not line[0].isspace() and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key:
                keys.add(key)
    return keys


def analyze(path: pathlib.Path) -> DocStats:
    """Compute structural stats for a Markdown file."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    fence_count = sum(1 for line in lines if FENCE_RE.match(line))
    return DocStats(
        h2_count=sum(1 for line in lines if H2_RE.match(line)),
        h3_count=sum(1 for line in lines if H3_RE.match(line)),
        code_blocks=fence_count // 2,
        front_matter_keys=parse_front_matter(lines),
        has_snippet=bool(SNIPPET_RE.search(text)),
    )


def collect_zh_files(docs_root: pathlib.Path) -> list[pathlib.Path]:
    """Collect zh Markdown files: ``docs/*.md`` and ``docs/commands/*.md``."""
    files: list[pathlib.Path] = []
    files.extend(sorted(docs_root.glob("*.md")))
    commands_dir = docs_root / "commands"
    if commands_dir.is_dir():
        files.extend(sorted(commands_dir.glob("*.md")))
    return files


def main() -> int:
    docs_root = pathlib.Path(__file__).resolve().parent.parent / "docs"
    if not docs_root.is_dir():
        print(f"ERROR: docs root not found: {docs_root}", file=sys.stderr)
        return 1

    zh_files = collect_zh_files(docs_root)
    if not zh_files:
        print("No zh docs found; nothing to check.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    for zh_path in zh_files:
        rel = zh_path.relative_to(docs_root)
        zh_stats = analyze(zh_path)
        for lang in LANGS:
            lang_path = docs_root / lang / rel
            if not lang_path.exists():
                warnings.append(f"WARNING [{lang}] missing {rel} (zh exists)")
                continue
            if zh_stats.has_snippet:
                # zh pulls in a root file via a snippet include (e.g.
                # ``--8<-- "CONTRIBUTING.md"``) and so has no headings/code
                # blocks of its own; en/ja are independently maintained full
                # translations. Only file existence is checked in this case.
                print(f"INFO [{lang}] {rel}: zh uses snippet, skip structure check")
                continue
            lang_stats = analyze(lang_path)
            if zh_stats.h2_count != lang_stats.h2_count:
                errors.append(
                    f"ERROR [{lang}] {rel}: H2 heading count mismatch "
                    f"(zh={zh_stats.h2_count}, {lang}={lang_stats.h2_count})"
                )
            if zh_stats.h3_count != lang_stats.h3_count:
                errors.append(
                    f"ERROR [{lang}] {rel}: H3 heading count mismatch "
                    f"(zh={zh_stats.h3_count}, {lang}={lang_stats.h3_count})"
                )
            if zh_stats.code_blocks != lang_stats.code_blocks:
                errors.append(
                    f"ERROR [{lang}] {rel}: code block count mismatch "
                    f"(zh={zh_stats.code_blocks}, {lang}={lang_stats.code_blocks})"
                )
            missing_keys = zh_stats.front_matter_keys - lang_stats.front_matter_keys
            if missing_keys:
                errors.append(
                    f"ERROR [{lang}] {rel}: missing front-matter keys "
                    f"{sorted(missing_keys)} (present in zh)"
                )

    for warning in warnings:
        print(warning)
    for error in errors:
        print(error)

    if errors:
        print(f"\ni18n sync: FAILED ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1

    print(f"i18n sync: OK ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
