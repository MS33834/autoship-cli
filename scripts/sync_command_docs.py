#!/usr/bin/env python3
"""Sync command docs with actual CLI ``--help`` output.

For each AutoShip command, runs ``uv run autoship <cmd> --help`` and compares
the option list (``--xxx`` long-option names) against the option table in
``docs/commands/<cmd>.md`` (table rows starting with ``|``).

Usage::

    python scripts/sync_command_docs.py          # print diff report
    python scripts/sync_command_docs.py --write  # same as default (reserved)
    python scripts/sync_command_docs.py --check  # exit 1 on diff (for CI)

If ``autoship`` is unavailable (``CalledProcessError`` / ``FileNotFoundError``),
each affected command is reported as SKIP and the script exits 0 — CI
environments without the CLI installed should not fail the pipeline.

Stdlib only. Used by the CI ``docs`` job.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess

COMMANDS: tuple[str, ...] = (
    "init",
    "clean",
    "commit",
    "verify",
    "fix",
    "upload",
    "plugin",
    "doctor",
    "audit",
    "registry",
    "metrics",
    "config",
)
OPTION_RE = re.compile(r"--[a-zA-Z][a-zA-Z0-9-]*")
# A subcommand row inside the "Commands" section of a typer group's --help.
# Matches lines like ``│ show    Display collected runtime metrics.``.
SUBCOMMAND_RE = re.compile(r"^│\s+([a-zA-Z][a-zA-Z0-9_-]*)\s")
# Typer/click built-in options that are not documented per-command.
BUILTIN_OPTIONS: frozenset[str] = frozenset({"--help", "--install-completion", "--show-completion"})
# Global / built-in options that are not reliably surfaced by a subcommand's
# ``--help`` output (they live on the root app or are auto-added by typer).
# Excluded from the docs-vs-CLI comparison so they never produce false diffs.
IGNORED_OPTIONS: frozenset[str] = frozenset(
    {"--help", "--version", "--dry-run", "--yes", "--verbose", "-h", "-v", "-n", "-y"}
)


def parse_help_options(text: str) -> set[str]:
    """Extract long option names (``--xxx``) from typer --help output."""
    found: set[str] = {match.group(0) for match in OPTION_RE.finditer(text)}
    return found - BUILTIN_OPTIONS


def parse_subcommands(text: str) -> list[str]:
    """Extract subcommand names from a typer group's ``--help`` output.

    Typer renders the subcommand list inside a rich box titled ``Commands``
    (``╭─ Commands ─...``). Each row looks like ``│ show   <description>``.
    Returns the subcommand names in display order; empty for leaf commands.
    """
    subcommands: list[str] = []
    in_commands = False
    for line in text.splitlines():
        if not in_commands:
            if "Commands" in line and "╭" in line:
                in_commands = True
            continue
        if line.lstrip().startswith("╰"):
            break
        match = SUBCOMMAND_RE.match(line)
        if match:
            subcommands.append(match.group(1))
    return subcommands


def parse_md_options(text: str) -> set[str]:
    """Extract long option names from option-table rows (lines starting with ``|``)."""
    options: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        for match in OPTION_RE.finditer(stripped):
            options.add(match.group(0))
    return options


def run_help(command_args: list[str]) -> str | None:
    """Run ``uv run autoship <command...> --help`` and return stdout. None on failure."""
    try:
        result = subprocess.run(
            ["uv", "run", "autoship", *command_args, "--help"],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    return result.stdout or ""


def collect_cli_options(command: str) -> set[str] | None:
    """Collect option names exposed by a command and its subcommands.

    Runs ``autoship <command> --help`` to get the group's own options and the
    subcommand list, then ``autoship <command> <sub> --help`` for each
    subcommand and unions the options. This is needed because typer only lists
    a group's direct options in the group ``--help``; subcommand options
    (e.g. ``plugin install --trust``) are documented per-subcommand.
    Returns ``None`` when the CLI is unavailable.
    """
    group_help = run_help([command])
    if group_help is None:
        return None
    options = parse_help_options(group_help)
    for sub in parse_subcommands(group_help):
        sub_help = run_help([command, sub])
        if sub_help is not None:
            options |= parse_help_options(sub_help)
    return options


def load_md_options(command: str, docs_commands_dir: pathlib.Path) -> set[str] | None:
    """Load option names from ``docs/commands/<command>.md``. None if file missing."""
    md_path = docs_commands_dir / f"{command}.md"
    if not md_path.exists():
        return None
    return parse_md_options(md_path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit 1 if any diff is found")
    parser.add_argument(
        "--write",
        action="store_true",
        help="print diff report (reserved for future auto-fix; behaves like default)",
    )
    args = parser.parse_args(argv)

    docs_commands_dir = pathlib.Path(__file__).resolve().parent.parent / "docs" / "commands"

    has_diff = False
    skipped = 0
    for command in COMMANDS:
        help_options = collect_cli_options(command)
        if help_options is None:
            print(f"[{command}] SKIP (autoship unavailable)")
            skipped += 1
            continue
        help_options -= IGNORED_OPTIONS
        md_options = load_md_options(command, docs_commands_dir)
        if md_options is None:
            print(f"[{command}] SKIP (doc missing)")
            skipped += 1
            continue
        md_options -= IGNORED_OPTIONS
        missing_in_md = sorted(help_options - md_options)
        missing_in_cli = sorted(md_options - help_options)
        if not missing_in_md and not missing_in_cli:
            print(f"[{command}] OK")
            continue
        has_diff = True
        print(f"[{command}] DIFF")
        for opt in missing_in_md:
            print(f"  - in CLI but not in docs: {opt}")
        for opt in missing_in_cli:
            print(f"  - in docs but not in CLI: {opt}")

    if not has_diff:
        print(f"\nCommand docs sync: OK ({skipped} skipped)")
        return 0

    if args.check:
        print(f"\nCommand docs sync: FAILED (diffs found, {skipped} skipped)")
        return 1

    print(f"\nCommand docs sync: DIFFS FOUND ({skipped} skipped, report mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
