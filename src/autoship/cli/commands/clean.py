"""The ``autoship clean`` command."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer

from autoship.adapters.tool_adapter import ToolChain
from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.exceptions import ToolChainError
from autoship.plugin_manager import manager as plugin_manager

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="clean")(clean)


_PYTHON_EXTENSIONS = frozenset({".py", ".pyi", ".pyx", ".pxd"})


def _builtin_format_file(file_path: Path) -> bool:
    """Apply built-in formatting to a single file.

    Returns True if the file was modified.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    original = content
    lines = content.splitlines(keepends=True)

    # 1. Strip trailing whitespace from each line
    lines = [
        (line.rstrip() + "\n") if line.endswith("\n") else line.rstrip()
        for line in lines
    ]

    # 2. Collapse multiple consecutive blank lines into a single blank line
    deduped: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        deduped.append(line)
        prev_blank = is_blank

    # 3. Ensure file ends with exactly one trailing newline
    new_content = "".join(deduped).rstrip("\n") + "\n"

    if new_content != original:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def _collect_python_files(paths: list[Path], project_root: Path) -> list[Path]:
    """Collect Python source files from the requested paths."""

    def _is_py(p: Path) -> bool:
        return p.suffix in _PYTHON_EXTENSIONS

    result: list[Path] = []
    for p in paths:
        target = (project_root / p).resolve() if not p.is_absolute() else p.resolve()
        if target.is_file() and _is_py(target):
            result.append(target)
        elif target.is_dir():
            result.extend(
                f for f in target.rglob("*.py") if f.is_file() and "__pycache__" not in f.parts
            )
    return result


@app.command()
def clean(
    ctx: typer.Context,
    paths: list[Path] = typer.Argument(default_factory=lambda: [Path(".")]),
    check: bool = typer.Option(False, "--check", help="Exit with error if changes are needed"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip interactive confirmations"),
) -> None:
    """Clean and format the project code."""
    config = ctx.obj["config"]
    i18n: I18n = get_i18n_from_ctx(ctx)
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes = yes or ctx.obj.get("yes", False)
    verbose: bool = ctx.obj.get("verbose", False)

    context = CommandContext(
        command="clean",
        project_root=config.project_root,
        config=config,
        dry_run=dry_run,
        yes=yes,
        trace_id=audit.trace_id,
    )

    audit.record("clean.start", {"paths": [str(p) for p in paths]})
    plugin_manager.call("pre_clean", context=context, fail_fast=False)

    toolchain = ToolChain(
        tools=config.clean.tools,
        project_root=config.project_root,
        dry_run=dry_run,
        verbose=verbose,
    )

    try:
        diff = toolchain.preview(paths)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise ToolChainError(i18n._("clean.preview_failed", exc=exc)) from exc

    if not diff.strip():
        # When external tools are missing, fall back to built-in formatting.
        missing = [t for t in config.clean.tools if shutil.which(t) is None]
        if missing and any(t in config.clean.tools for t in ("autoflake", "black")):
            typer.echo(
                i18n._("clean.builtin_fallback", tools=", ".join(sorted(missing))),
                err=True,
            )
            py_files = _collect_python_files(paths, config.project_root)
            changed = 0
            for f in py_files:
                if dry_run:
                    typer.echo(f"[dry-run] would format {f}")
                    changed += 1
                elif _builtin_format_file(f):
                    changed += 1
                    if verbose:
                        typer.echo(f"Formatted: {f}")
            if changed:
                audit.record("clean.builtin", {"changed": changed})
                typer.echo(i18n._("clean.builtin_done", count=changed))
                plugin_manager.call("post_clean", context=context, fail_fast=False)
            else:
                audit.record("clean.noop")
                typer.echo(i18n._("clean.noop"))
            return

        typer.echo(i18n._("clean.noop"))
        audit.record("clean.noop")
        return

    if verbose or dry_run:
        typer.echo(diff)

    if check:
        raise ToolChainError(i18n._("clean.not_clean"))

    if not dry_run and not yes and not typer.confirm(i18n._("clean.confirm")):
        typer.echo(i18n._("clean.aborted"))
        audit.record("clean.aborted", {"reason": "user_declined"})
        raise typer.Exit(code=0)

    try:
        toolchain.apply(paths)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise ToolChainError(i18n._("clean.apply_failed", exc=exc)) from exc

    audit.record("clean.done", {"paths": [str(p) for p in paths]})
    plugin_manager.call("post_clean", context=context, fail_fast=False)
    typer.echo(i18n._("clean.complete"))
