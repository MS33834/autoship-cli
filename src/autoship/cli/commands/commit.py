"""The ``autoship commit`` command."""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

import typer

from autoship.adapters.git_adapter import GitAdapter
from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.model_router import ModelRouter
from autoship.exceptions import GitError, ModelGatewayError
from autoship.plugin_manager import manager as plugin_manager

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="commit")(commit)


@app.command()
def commit(
    ctx: typer.Context,
    message: str | None = typer.Option(None, "--message", "-m", help="Use given commit message"),
    edit: bool = typer.Option(True, "--edit/--no-edit", help="Open editor to refine message"),
) -> None:
    """Generate a commit message and commit staged/unstaged changes."""
    config = ctx.obj["config"]
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)
    verbose: bool = ctx.obj.get("verbose", False)

    git = GitAdapter(config.project_root)

    if not git.has_changes():
        typer.echo("Nothing to commit.")
        return

    context = CommandContext(
        command="commit",
        project_root=config.project_root,
        config=config,
        dry_run=dry_run,
        yes=yes,
        trace_id=audit.trace_id,
    )

    audit.record("commit.start")
    plugin_manager.call("pre_commit", context=context, fail_fast=False)

    diff = git.diff()
    stats = git.stats()

    final_message = message
    if final_message is None:
        router = ModelRouter(config)
        try:
            final_message = router.generate_commit_message(diff=diff, stats=stats)
        except ModelGatewayError as exc:
            if verbose:
                typer.echo(f"Model message generation failed: {exc}", err=True)
            final_message = "Update files"

    if edit and not yes:
        final_message = _open_editor(final_message)

    if dry_run:
        typer.echo(f"[dry-run] Would commit with message:\n{final_message}")
        audit.record("commit.dry_run", {"message": final_message})
        return

    git.commit(final_message)

    audit.record("commit.done", {"message": final_message})
    plugin_manager.call("post_commit", context=context, fail_fast=False)
    typer.echo(f"Committed: {final_message}")


def _open_editor(initial: str) -> str:
    """Open the user's preferred editor to review/modify a commit message."""
    editor = os.environ.get("EDITOR", "vim")
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as f:
        f.write(initial)
        f.flush()
        path = Path(f.name)
    try:
        subprocess.run([*shlex.split(editor), str(path)], check=True)
        return path.read_text(encoding="utf-8").strip()
    except subprocess.CalledProcessError as exc:
        raise GitError(
            f"Editor exited with code {exc.returncode}; commit message was not saved."
        ) from exc
    finally:
        path.unlink(missing_ok=True)
