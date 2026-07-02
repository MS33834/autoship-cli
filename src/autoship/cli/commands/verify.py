"""The ``autoship verify`` command."""

from __future__ import annotations

import logging
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import typer

from autoship.core.audit_logger import AuditLogger, redact_text
from autoship.core.context import CommandContext
from autoship.core.fix import FixSuggestion
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.tool_verifier import ToolVerifier
from autoship.exceptions import ConfigError, VerifyError
from autoship.models.config import ToolsConfig, VerifyConfig
from autoship.plugin_manager import manager as plugin_manager
from autoship.utils.permissions import ensure_dir_permissions, ensure_file_permissions

ERROR_LOG_DIR = Path.home() / ".local" / "state" / "autoship"
ERROR_LOG_PATH = ERROR_LOG_DIR / "last_error.txt"

# Shell metacharacters that are never allowed in a verification command string.
_FORBIDDEN_SHELL_CHARS = re.compile(r"[;|&$`<>\n]")

logger = logging.getLogger("autoship")


def _write_error_log(stdout: str, stderr: str) -> None:
    """Persist redacted verify output with restrictive permissions.

    stdout/stderr are redacted using the same logic as the audit logger before
    being written. The containing directory is created with ``0o700`` and the
    log file with ``0o600``. Existing paths with overly broad permissions are
    tightened and a warning is emitted.
    """
    try:
        ensure_dir_permissions(ERROR_LOG_DIR, 0o700)
        content = f"STDOUT:\n{redact_text(stdout)}\n\nSTDERR:\n{redact_text(stderr)}"
        ERROR_LOG_PATH.write_text(content, encoding="utf-8")
        ensure_file_permissions(ERROR_LOG_PATH, 0o600)
    except OSError:
        pass


def _validate_verify_command(command: str, verify_config: VerifyConfig, i18n: I18n) -> list[str]:
    """Validate ``command`` against the configured allowlist.

    Returns the split command list on success, or raises ``VerifyError`` if the
    command contains shell metacharacters or the executable is not in the
    configured allowlist.
    """
    if _FORBIDDEN_SHELL_CHARS.search(command):
        raise VerifyError(
            i18n._("verify.command_disallowed", command=command),
            details={"command": command, "reason": "shell_metacharacters"},
        )

    try:
        cmd_parts = shlex.split(command)
    except ValueError as exc:
        raise VerifyError(
            i18n._("verify.command_disallowed", command=command),
            details={"command": command, "reason": str(exc)},
        ) from exc

    if not cmd_parts:
        raise VerifyError(
            i18n._("verify.command_disallowed", command=command),
            details={"command": command, "reason": "empty_command"},
        )

    executable_name = Path(cmd_parts[0]).name
    allowed = verify_config.allowed_commands
    if executable_name not in allowed:
        raise VerifyError(
            i18n._("verify.command_disallowed", command=command),
            details={"command": command, "executable": executable_name, "allowed": allowed},
        )

    return cmd_parts


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
    i18n: I18n = get_i18n_from_ctx(ctx)
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
        typer.echo(i18n._("verify.dry_run", command=command))
        audit.record("verify.dry_run", {"command": command})
        plugin_manager.call("post_verify", context=context, fail_fast=False)
        raise typer.Exit(code=0)

    cmd_parts = _validate_verify_command(command, config.verify, i18n)
    executable = shutil.which(cmd_parts[0])
    if executable is None:
        error = VerifyError(
            i18n._("verify.command_not_found", cmd=cmd_parts[0]),
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
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        audit.record("verify.error", {"command": command, "error": str(exc)})
        _handle_error(context, exc, audit, i18n)
        raise VerifyError(i18n._("verify.run_failed", exc=exc)) from exc

    stdout_redacted = redact_text(result.stdout)
    stderr_redacted = redact_text(result.stderr)

    if verbose:
        typer.echo(stdout_redacted)
    if result.stderr:
        typer.secho(stderr_redacted, fg=typer.colors.YELLOW, err=True)

    if result.returncode != 0:
        _write_error_log(result.stdout, result.stderr)
        audit.record(
            "verify.failure",
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": stdout_redacted,
                "stderr": stderr_redacted,
            },
        )
        error = VerifyError(
            i18n._(
                "verify.failed",
                code=result.returncode,
                command=command,
            ),
            details={
                "command": command,
                "stdout": stdout_redacted,
                "stderr": stderr_redacted,
            },
        )
        _handle_error(context, error, audit, i18n)
        raise error

    audit.record("verify.done", {"command": command})
    plugin_manager.call("post_verify", context=context, fail_fast=False)
    typer.echo(i18n._("verify.verified", command=command))


def _handle_error(
    context: CommandContext, error: Exception, audit: AuditLogger, i18n: I18n
) -> None:
    """Invoke ``on_error`` hooks and optionally apply fix patches."""
    hook_results = plugin_manager.call("on_error", context=context, error=error, fail_fast=False)

    if not context.extras.get("fix"):
        return

    suggestions: list[FixSuggestion] = [
        suggestion for suggestion in hook_results if isinstance(suggestion, FixSuggestion)
    ]

    for index, suggestion in enumerate(suggestions, start=1):
        _present_suggestion(context, suggestion, index, audit, i18n)


def _present_suggestion(
    context: CommandContext,
    suggestion: FixSuggestion,
    index: int,
    audit: AuditLogger,
    i18n: I18n,
) -> None:
    """Display a fix suggestion and apply its patch if the user confirms."""
    typer.secho(f"\n{i18n._('verify.suggested_fix', index=index)}", fg=typer.colors.CYAN)
    typer.echo(suggestion.description)

    if not suggestion.patch:
        audit.record("verify.fix.suggestion", {"description": suggestion.description})
        return

    typer.secho(f"\n{i18n._('verify.proposed_patch')}", fg=typer.colors.CYAN)
    typer.echo(suggestion.patch)

    if context.dry_run:
        audit.record(
            "verify.fix.dry_run",
            {"description": suggestion.description, "patch": suggestion.patch},
        )
        typer.echo(i18n._("verify.patch_dry_run"))
        return

    if not context.yes and not typer.confirm(i18n._("verify.apply_patch")):
        audit.record(
            "verify.fix.declined",
            {"description": suggestion.description},
        )
        typer.echo(i18n._("verify.patch_not_applied"))
        return

    applied, reason = _apply_patch(context.project_root, suggestion.patch, context.config.tools)
    if applied:
        audit.record(
            "verify.fix.applied",
            {"description": suggestion.description, "patch": suggestion.patch},
        )
        typer.echo(i18n._("verify.patch_applied"))
    else:
        audit.record(
            "verify.fix.failed",
            {"description": suggestion.description, "patch": suggestion.patch, "reason": reason},
        )
        typer.secho(i18n._("verify.patch_failed", reason=reason), fg=typer.colors.YELLOW, err=True)


def _apply_patch(
    project_root: Path,
    patch: str,
    tools: ToolsConfig | None = None,
) -> tuple[bool, str | None]:
    """Apply a unified diff patch to the project.

    Prefers ``git apply`` and falls back to the ``patch`` command so patches
    can still be applied when the working tree differs from HEAD. Returns a
    tuple of ``(success, reason)`` so callers can explain failures.

    When ``tools`` is provided the pinned binary paths / hashes from
    ``config.tools`` are honoured via :class:`ToolVerifier`.
    """
    last_reason: str | None = None

    verifier = ToolVerifier(tools) if tools else ToolVerifier()

    try:
        git = verifier.resolve("git")
    except ConfigError:
        git = None

    if git:
        check = subprocess.run(
            [git, "apply", "--check"],
            input=patch,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if check.returncode == 0:
            apply = subprocess.run(
                [git, "apply"],
                input=patch,
                cwd=project_root,
                capture_output=True,
                text=True,
            )
            if apply.returncode == 0:
                return True, None
            last_reason = apply.stderr.strip() or "git apply failed"
        else:
            last_reason = check.stderr.strip() or "git apply --check failed"

    try:
        patch_cmd = verifier.resolve("patch")
    except ConfigError:
        patch_cmd = None

    if patch_cmd:
        proc = subprocess.run(
            [patch_cmd, "-p1"],
            input=patch,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return True, None
        last_reason = proc.stderr.strip() or "patch command failed"

    return False, last_reason or "Neither git nor patch is available on PATH"
