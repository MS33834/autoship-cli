"""The ``autoship verify`` command."""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

import typer

from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.exceptions import VerifyError
from autoship.plugin_manager import manager as plugin_manager

app = typer.Typer()


def register(parent: typer.Typer) -> None:
    parent.command(name="verify")(verify)


@app.command(name="verify")
def verify(
    ctx: typer.Context,
    command: str = typer.Argument(..., help="Command to run for verification, e.g. `pytest`"),
    fix: bool = typer.Option(False, "--fix", help="Ask the model to suggest fixes on failure"),
) -> None:
    """Run a verification command and capture errors for AI-assisted fixing."""
    config = ctx.obj["config"]
    audit: AuditLogger = ctx.obj["audit_logger"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes: bool = ctx.obj.get("yes", False)
    verbose: bool = ctx.obj.get("verbose", False)

    context = CommandContext(
        command="verify",
        project_root=config.project_root,
        config=config,
        dry_run=dry_run,
        yes=yes,
        trace_id=audit.trace_id,
        extras={"verify_command": command, "fix": fix},
    )

    audit.record("verify.start", {"command": command, "fix": fix})
    plugin_manager.call("pre_verify", context=context, fail_fast=False)

    if dry_run:
        typer.echo(f"[dry-run] Would run: {command}")
        audit.record("verify.dry_run", {"command": command})
        plugin_manager.call("post_verify", context=context, fail_fast=False)
        raise typer.Exit(code=0)

    cmd_parts = shlex.split(command)
    executable = shutil.which(cmd_parts[0])
    if executable is None:
        error = VerifyError(
            f"Verification command not found on PATH: {cmd_parts[0]}",
            details={"command": command},
        )
        audit.record("verify.error", {"command": command, "error": str(error)})
        raise error

    try:
        result = subprocess.run(
            cmd_parts,
            cwd=config.project_root,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as exc:
        audit.record("verify.error", {"command": command, "error": str(exc)})
        _handle_error(context, exc, audit)
        raise VerifyError(f"Failed to run verification command: {exc}") from exc

    if verbose:
        typer.echo(result.stdout)
    if result.stderr:
        typer.secho(result.stderr, fg=typer.colors.YELLOW, err=True)

    if result.returncode != 0:
        audit.record(
            "verify.failure",
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )
        error = VerifyError(
            f"Verification failed with exit code {result.returncode}",
            details={"command": command, "stdout": result.stdout, "stderr": result.stderr},
        )
        _handle_error(context, error, audit)
        raise error

    audit.record("verify.done", {"command": command})
    plugin_manager.call("post_verify", context=context, fail_fast=False)
    typer.echo(f"Verified: {command}")


def _handle_error(context: CommandContext, error: Exception, audit: AuditLogger) -> None:
    """Invoke ``on_error`` hooks and optionally apply fix patches."""
    hook_results = plugin_manager.call("on_error", context=context, error=error, fail_fast=False)

    if not context.extras.get("fix"):
        return

    suggestions: list[FixSuggestion] = [
        suggestion for suggestion in hook_results if isinstance(suggestion, FixSuggestion)
    ]

    for index, suggestion in enumerate(suggestions, start=1):
        _present_suggestion(context, suggestion, index, audit)


def _present_suggestion(
    context: CommandContext,
    suggestion: FixSuggestion,
    index: int,
    audit: AuditLogger,
) -> None:
    """Display a fix suggestion and apply its patch if the user confirms."""
    typer.secho(f"\nSuggested fix {index}:", fg=typer.colors.CYAN)
    typer.echo(suggestion.description)

    if not suggestion.patch:
        audit.record("verify.fix.suggestion", {"description": suggestion.description})
        return

    typer.secho("\nProposed patch:", fg=typer.colors.CYAN)
    typer.echo(suggestion.patch)

    if context.dry_run:
        audit.record(
            "verify.fix.dry_run",
            {"description": suggestion.description, "patch": suggestion.patch},
        )
        typer.echo("[dry-run] Patch not applied.")
        return

    if not context.yes and not typer.confirm("Apply this patch?"):
        audit.record(
            "verify.fix.declined",
            {"description": suggestion.description},
        )
        typer.echo("Patch not applied.")
        return

    applied, reason = _apply_patch(context.project_root, suggestion.patch)
    if applied:
        audit.record(
            "verify.fix.applied",
            {"description": suggestion.description, "patch": suggestion.patch},
        )
        typer.echo("Patch applied.")
    else:
        audit.record(
            "verify.fix.failed",
            {"description": suggestion.description, "patch": suggestion.patch, "reason": reason},
        )
        typer.secho(f"Failed to apply patch: {reason}", fg=typer.colors.YELLOW, err=True)


def _apply_patch(project_root: Path, patch: str) -> tuple[bool, str | None]:
    """Apply a unified diff patch to the project.

    Prefers ``git apply`` and falls back to the ``patch`` command. Returns a
    tuple of ``(success, reason)`` so callers can explain failures.
    """
    if shutil.which("git"):
        check = subprocess.run(
            ["git", "apply", "--check"],
            input=patch,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if check.returncode == 0:
            apply = subprocess.run(
                ["git", "apply"],
                input=patch,
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if apply.returncode == 0:
                return True, None
            return False, apply.stderr.strip() or "git apply failed"
        return False, check.stderr.strip() or "git apply --check failed"

    if shutil.which("patch"):
        proc = subprocess.run(
            ["patch", "-p1"],
            input=patch,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return True, None
        return False, proc.stderr.strip() or "patch command failed"

    return False, "Neither git nor patch is available on PATH"
