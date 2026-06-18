"""The ``autoship verify`` command."""

from __future__ import annotations

import shlex
import shutil
import subprocess

import typer

from autoship.core.audit_logger import AuditLogger
from autoship.core.context import CommandContext
from autoship.exceptions import ModelGatewayError, VerifyError
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
        plugin_manager.call("on_error", context=context, error=exc, fail_fast=False)
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
        plugin_manager.call("on_error", context=context, error=error, fail_fast=False)

        if fix:
            _suggest_fix(context, command, result.stdout, result.stderr)

        raise error

    audit.record("verify.done", {"command": command})
    plugin_manager.call("post_verify", context=context, fail_fast=False)
    typer.echo(f"Verified: {command}")


def _suggest_fix(
    context: CommandContext,
    command: str,
    stdout: str,
    stderr: str,
) -> None:
    """Print an AI-generated fix suggestion without blocking the exit code."""
    from autoship.adapters.model_gateway import ChatMessage
    from autoship.core.model_router import ModelRouter

    router = ModelRouter(context.config)
    prompt = (
        "The following verification command failed. "
        "Suggest a concise fix in one or two sentences.\n\n"
        f"Command: {command}\n\n"
        f"stdout:\n{stdout[-4000:]}\n\n"
        f"stderr:\n{stderr[-4000:]}"
    )
    try:
        suggestion = router.chat(
            [
                ChatMessage(role="system", content="You are a helpful debugging assistant."),
                ChatMessage(role="user", content=prompt),
            ],
            "verify-fix",
        )
        typer.secho("\nSuggested fix:", fg=typer.colors.CYAN)
        typer.echo(suggestion)
    except ModelGatewayError as exc:
        typer.secho(f"Could not generate fix suggestion: {exc}", fg=typer.colors.YELLOW, err=True)
