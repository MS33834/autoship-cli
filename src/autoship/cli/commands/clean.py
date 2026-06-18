"""The ``autoship clean`` command."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from autoship.adapters.tool_adapter import ToolChain
from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.exceptions import ToolChainError
from autoship.plugin_manager import manager as plugin_manager

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="clean")(clean)


@app.command()
def clean(
    ctx: typer.Context,
    paths: list[Path] = typer.Argument(default_factory=lambda: [Path(".")]),
    check: bool = typer.Option(False, "--check", help="Exit with error if changes are needed"),
) -> None:
    """Clean and format the project code."""
    config = ctx.obj["config"]
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)
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
        raise ToolChainError(f"Failed to preview clean changes: {exc}") from exc

    if not diff.strip():
        typer.echo("Already clean.")
        audit.record("clean.noop")
        return

    if verbose or dry_run:
        typer.echo(diff)

    if check:
        raise ToolChainError("Code is not clean; run `autoship clean`.")

    if not dry_run and not yes and not typer.confirm("Apply formatting changes?"):
        typer.echo("Aborted.")
        audit.record("clean.aborted", {"reason": "user_declined"})
        raise typer.Exit(code=0)

    try:
        toolchain.apply(paths)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        raise ToolChainError(f"Failed to apply clean changes: {exc}") from exc

    audit.record("clean.done", {"paths": [str(p) for p in paths]})
    plugin_manager.call("post_clean", context=context, fail_fast=False)
    typer.echo("Clean complete.")
