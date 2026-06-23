"""The ``autoship fix`` command."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import typer
from pydantic import HttpUrl

from autoship.adapters.model_gateway import ChatMessage
from autoship.core.i18n import I18n, get_i18n_from_ctx
from autoship.core.model_router import ModelRouter
from autoship.exceptions import ModelGatewayError
from autoship.models.config import (
    AppConfig,
    LlmProvider,
    ModelBackendConfig,
    Provider,
)

app = typer.Typer()

ERROR_LOG_PATH = Path.home() / ".local" / "state" / "autoship" / "last_error.txt"

ALLOWED_EXTENSIONS = {
    ".py",
    ".toml",
    ".cfg",
    ".ini",
    ".yaml",
    ".yml",
    ".json",
}
MAX_FILE_SIZE = 50 * 1024  # 50 KiB


SYSTEM_PROMPT = (
    "You are an expert software engineer. A verification command failed. "
    "Analyze the error output and project context, then propose a concrete fix. "
    "Respond with a brief explanation followed by a unified diff patch that can "
    "be applied with `git apply` or `patch -p1`. "
    "Fix the implementation/source code, NEVER the tests: do not modify any file "
    "whose path contains 'tests/' or 'test_'. If the error is clearly caused by a "
    "bug in a test, explain that instead of producing a patch. "
    "If you cannot produce a patch, explain what the user should check manually."
)


_LLM_PROVIDER_TO_BACKEND: dict[LlmProvider, Provider] = {
    LlmProvider.OPENAI: Provider.OPENAI,
    LlmProvider.OPENROUTER: Provider.OPENROUTER,
    LlmProvider.OLLAMA: Provider.OLLAMA,
}

_DEFAULT_BASE_URLS: dict[Provider, str] = {
    Provider.OPENAI: "https://api.openai.com/v1",
    Provider.OPENROUTER: "https://openrouter.ai/api/v1",
    Provider.OLLAMA: "http://127.0.0.1:11434/v1",
}


def _model_router(config: AppConfig) -> ModelRouter:
    """Return a ModelRouter using configured backends or legacy [llm] config."""
    if not config.model.backends and config.llm.provider in _LLM_PROVIDER_TO_BACKEND:
        backend_provider = _LLM_PROVIDER_TO_BACKEND[config.llm.provider]
        base_url = config.llm.base_url or cast(HttpUrl, _DEFAULT_BASE_URLS[backend_provider])
        legacy_backend = ModelBackendConfig(
            provider=backend_provider,
            base_url=base_url,
            api_key=config.llm.api_key,
            api_version=config.llm.api_version,
            model=config.llm.model,
            timeout=config.llm.timeout,
        )
        compat_model = config.model.model_copy(update={"backends": [legacy_backend]})
        compat_config = config.model_copy(update={"model": compat_model})
        return ModelRouter(compat_config)
    return ModelRouter(config)


def register(parent: typer.Typer) -> None:
    parent.command(name="fix")(fix)


@app.command(name="fix")
def fix(
    ctx: typer.Context,
    error_file: Path | None = typer.Argument(
        None, help="Path to error log (defaults to last verify output)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmations"),
) -> None:
    """Ask an LLM to propose a fix for the last verification failure."""
    i18n: I18n = get_i18n_from_ctx(ctx)
    config = ctx.obj["config"]
    dry_run: bool = ctx.obj.get("dry_run", False)
    yes = yes or ctx.obj.get("yes", False)

    source = error_file or ERROR_LOG_PATH
    if not source.exists():
        raise typer.BadParameter(i18n._("fix.no_error_log", path=str(source)))

    error_context = source.read_text(encoding="utf-8")
    if not error_context.strip():
        raise typer.BadParameter(i18n._("fix.empty_error_log", path=str(source)))

    user_prompt, read_paths = _build_prompt(error_context, config.project_root)
    if read_paths:
        typer.echo(i18n._("fix.reading_files", files=", ".join(read_paths)))

    if dry_run:
        typer.echo(i18n._("fix.dry_run", files=", ".join(read_paths) if read_paths else "-"))
        return

    typer.echo(i18n._("fix.thinking"))
    router = _model_router(config)
    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]
    try:
        response = router.chat(messages, "fix")
    except ModelGatewayError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo("\n" + response)

    patch = _extract_patch(response)
    if patch and (yes or typer.confirm(i18n._("fix.apply_patch"))):
        _apply_patch(config.project_root, patch, i18n)


def _build_prompt(error_context: str, project_root: Path) -> tuple[str, list[str]]:
    relevant_files, read_paths = _collect_relevant_files(project_root, error_context)
    files_section = ""
    if relevant_files:
        files_section = "\n\nRelevant project files:\n" + "\n".join(
            f"--- {path} ---\n{content[:2000]}" for path, content in relevant_files.items()
        )
    prompt = f"Verification failed with the following output:\n\n{error_context}{files_section}"
    return prompt, read_paths


def _is_within_project(path: Path, project_root: Path) -> bool:
    """Return True when ``path`` resolves to a location inside ``project_root``."""
    try:
        resolved = path.resolve()
        root = project_root.resolve()
        return resolved.is_relative_to(root)
    except (OSError, ValueError, RuntimeError):
        return False


def _collect_relevant_files(
    project_root: Path, error_context: str
) -> tuple[dict[str, str], list[str]]:
    """Best-effort extraction of file paths from the error context.

    Only files that resolve inside ``project_root``, have an allowed extension,
    and are smaller than ``MAX_FILE_SIZE`` are returned.
    """
    files: dict[str, str] = {}
    read_paths: list[str] = []
    root = project_root.resolve()

    for token in error_context.split():
        token = token.strip("'\":(),")
        if not token or ".." in Path(token).parts:
            continue

        path = Path(token)
        if not path.is_absolute():
            path = project_root / path

        if not _is_within_project(path, project_root):
            continue

        resolved = path.resolve()
        if resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if not resolved.is_file():
            continue

        try:
            if resolved.stat().st_size > MAX_FILE_SIZE:
                continue
            content = resolved.read_text(encoding="utf-8")
            rel = resolved.relative_to(root)
            rel_str = str(rel)
            if rel_str not in files:
                files[rel_str] = content
                read_paths.append(rel_str)
        except (OSError, ValueError):
            continue

        if len(files) >= 3:
            break

    return files, read_paths


def _extract_patch(response: str) -> str | None:
    """Extract a unified diff from the LLM response if present.

    Preserves internal indentation and trailing newlines so the patch can be
    applied by ``git apply`` or ``patch -p1``.
    """
    fence_start = response.find("```diff")
    if fence_start == -1:
        fence_start = response.find("```patch")
        offset = 8
    else:
        offset = 7

    if fence_start == -1:
        plain_start = response.find("--- ")
        if plain_start == -1:
            return None
        patch = response[plain_start:].rstrip()
        return (patch + "\n") if patch else None

    content = response[fence_start + offset :]
    fence_end = content.find("```")
    if fence_end != -1:
        content = content[:fence_end]

    lines = content.splitlines()
    # Drop leading blank lines introduced by the code fence, but keep all
    # indentation and trailing newlines required by patch(1).
    while lines and not lines[0].strip():
        lines.pop(0)
    patch = "\n".join(lines)
    return (patch + "\n") if patch else None


def _collect_patch_paths(patch: str) -> set[str]:
    """Return the file paths referenced in a unified diff."""
    paths: set[str] = set()
    for line in patch.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            # Strip the optional timestamp suffix that ``git diff`` appends.
            raw = line[4:].split("\t", 1)[0].strip()
            if raw in ("/dev/null", "dev/null"):
                continue
            # Unified diffs prefix old paths with ``a/`` and new paths with ``b/``.
            if raw.startswith("a/") or raw.startswith("b/"):
                raw = raw[2:]
            paths.add(raw)
    return paths


def _patch_paths_are_safe(project_root: Path, patch: str) -> bool:
    """Return True when every path in ``patch`` stays inside ``project_root``.

    Also rejects patches that would modify test files, keeping the fix command
    focused on implementation/source code only.
    """
    root = project_root.resolve()
    for raw in _collect_patch_paths(patch):
        # Reject absolute paths and path traversal attempts outright.
        if Path(raw).is_absolute() or ".." in Path(raw).parts:
            return False
        if not (root / raw).resolve().is_relative_to(root):
            return False
        raw_lower = raw.lower()
        if "tests/" in raw_lower or "test_" in raw_lower or raw_lower.startswith("test"):
            return False
    return True


def _apply_patch(project_root: Path, patch: str, i18n: I18n) -> None:
    import shutil
    import subprocess

    if not _patch_paths_are_safe(project_root, patch):
        typer.secho(
            i18n._("fix.patch_unsafe_paths"),
            fg=typer.colors.YELLOW,
            err=True,
        )
        return

    last_reason: str | None = None

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
            last_reason = apply.stderr.strip() or "git apply failed"
        else:
            last_reason = check.stderr.strip() or "git apply --check failed"

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
        last_reason = proc.stderr.strip() or "patch command failed"

    if last_reason:
        typer.secho(
            i18n._("fix.patch_failed", reason=last_reason),
            fg=typer.colors.YELLOW,
            err=True,
        )
    else:
        typer.secho(i18n._("fix.patch_no_tool"), fg=typer.colors.YELLOW, err=True)
