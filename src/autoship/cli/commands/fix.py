"""The ``autoship fix`` command."""

from __future__ import annotations

from pathlib import Path

import typer

from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.llm_client import LlmClient
from autoship.exceptions import ModelGatewayError

app = typer.Typer()

ERROR_LOG_PATH = Path.home() / ".local" / "state" / "autoship" / "last_error.txt"

SYSTEM_PROMPT = (
    "You are an expert software engineer. A verification command failed. "
    "Analyze the error output and project context, then propose a concrete fix. "
    "Respond with a brief explanation followed by a unified diff patch that can "
    "be applied with `git apply` or `patch -p1`. If you cannot produce a patch, "
    "explain what the user should check manually."
)


def register(parent: typer.Typer) -> None:
    parent.command(name="fix")(fix)


@app.command(name="fix")
def fix(
    ctx: typer.Context,
    error_file: Path | None = typer.Argument(None, help="Path to error log (defaults to last verify output)"),
    apply: bool = typer.Option(False, "--apply", help="Apply the generated patch without prompting"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Ask an LLM to propose a fix for the last verification failure."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    config = ctx.obj["config"]

    source = error_file or ERROR_LOG_PATH
    if not source.exists():
        raise typer.BadParameter(i18n._("fix.no_error_log", path=str(source)))

    error_context = source.read_text(encoding="utf-8")
    if not error_context.strip():
        raise typer.BadParameter(i18n._("fix.empty_error_log", path=str(source)))

    if not config.llm.api_key and config.llm.provider.value in ("openai", "openrouter"):
        raise typer.BadParameter(i18n._("fix.missing_api_key", provider=config.llm.provider.value))

    user_prompt = _build_prompt(error_context, config.project_root)

    typer.echo(i18n._("fix.thinking"))
    client = LlmClient(config.llm)
    try:
        response = client.chat(SYSTEM_PROMPT, user_prompt)
    except ModelGatewayError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo("\n" + response)

    patch = _extract_patch(response)
    if patch and (apply or yes or typer.confirm(i18n._("fix.apply_patch"))):
        _apply_patch(config.project_root, patch, i18n)


def _build_prompt(error_context: str, project_root: Path) -> str:
    relevant_files = _collect_relevant_files(project_root, error_context)
    files_section = ""
    if relevant_files:
        files_section = "\n\nRelevant project files:\n" + "\n".join(
            f"--- {path} ---\n{content[:2000]}" for path, content in relevant_files.items()
        )
    return f"Verification failed with the following output:\n\n{error_context}{files_section}"


def _collect_relevant_files(project_root: Path, error_context: str) -> dict[str, str]:
    """Best-effort extraction of file paths from the error context."""
    files: dict[str, str] = {}
    for token in error_context.split():
        token = token.strip("'\":(),")
        path = Path(token)
        if not path.is_absolute():
            path = project_root / path
        if path.exists() and path.is_file() and path.suffix in {".py", ".toml", ".cfg", ".ini", ".yaml", ".yml"}:
            try:
                rel = path.relative_to(project_root)
                files[str(rel)] = path.read_text(encoding="utf-8")
            except (OSError, ValueError):
                continue
        if len(files) >= 3:
            break
    return files


def _extract_patch(response: str) -> str | None:
    """Extract a unified diff from the LLM response if present."""
    start = response.find("```diff")
    if start == -1:
        start = response.find("--- ")
        if start == -1:
            return None
        return response[start:].strip()

    end = response.find("```", start + 7)
    if end == -1:
        return response[start + 7:].strip()
    return response[start + 7:end].strip()


def _apply_patch(project_root: Path, patch: str, i18n: I18n) -> None:
    import shutil
    import subprocess

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
                typer.echo(i18n._("fix.patch_applied"))
                return
            typer.secho(i18n._("fix.patch_failed", reason=apply.stderr.strip()), fg=typer.colors.YELLOW, err=True)
            return
        typer.secho(i18n._("fix.patch_failed", reason=check.stderr.strip()), fg=typer.colors.YELLOW, err=True)
        return

    if shutil.which("patch"):
        proc = subprocess.run(
            ["patch", "-p1"],
            input=patch,
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            typer.echo(i18n._("fix.patch_applied"))
            return
        typer.secho(i18n._("fix.patch_failed", reason=proc.stderr.strip()), fg=typer.colors.YELLOW, err=True)
        return

    typer.secho(i18n._("fix.patch_no_tool"), fg=typer.colors.YELLOW, err=True)
