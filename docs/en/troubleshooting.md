---
title: Troubleshooting
---
# Troubleshooting

> This page lists common AutoShip failures and how to diagnose them. Start with `autoship doctor` for a quick self-check, then match against the sections below. Command code blocks are kept in English.

## Installation Failures

### `autoship` command not found (PATH issue)

```bash
pipx list
pipx ensurepath
```

`pipx ensurepath` writes the pipx bin directory to PATH. After running it, **reopen your terminal** or `source` your shell config (`~/.bashrc` / `~/.zshrc`) and try again.

### Conflict between pipx and system pip

If you previously installed an old version via `pip install autoship`, the old path may take precedence:

```bash
pip uninstall autoship
pipx install autoship
which -a autoship
```

### Insufficient permissions / EACCES

Avoid `sudo pip install`. Recommended:

```bash
pipx install autoship
# or
uv tool install autoship
```

If you must use pip, first confirm the user directory reported by `python -m site --user-base` is writable.

## `init` Hangs

### Interactive questionnaire hangs

`init` asks several questions by default. In CI or scripts, skip them with `--yes`:

```bash
autoship init --yes
```

### Stuck on "detecting model backend"

`init` tries to probe local Ollama / LM Studio. If the backend is not running it waits for a timeout. You can:

- Start Ollama and retry;
- Or skip probing with `--no-model` and configure the backend in `.autoship.toml` later.

## Recovering from `clean` Mis-deletes

Before removing unused imports / reordering code, `clean` backs up changes prior to Git staging. If you notice a wrong deletion:

```bash
# View changes
git diff

# Discard clean's changes, restore to HEAD
git checkout -- .

# If already committed, revert once
git reset --hard HEAD~1
```

> Recommended: run `git status` before `clean` to confirm a clean working tree, or add `--dry-run` to preview.

## `commit` Empty Message / Timeout

### Generated commit message is empty

- Confirm there are staged changes: `git diff --cached`.
- If using an AI backend, check whether it is available (see below).
- Temporarily fall back to template mode:

```bash
autoship commit --no-ai
```

### AI generation timeout

An overly large model or slow backend may cause a timeout. Adjust in `.autoship.toml`:

```toml
[commit]
timeout_seconds = 60
```

Or switch to a smaller local model.

## `verify --fix` Cannot Connect to Backend

`verify --fix` requires an available AI backend, otherwise it reports "no AI backend configured".

```bash
# 1. Check backend status
autoship doctor

# 2. Confirm Ollama is running
ollama list

# 3. Use verbose to see detailed errors
autoship --verbose verify --fix pytest
```

See [Known Issues](known-issues.md) for "`verify --fix` unavailable without an AI backend".

## `upload` Credential Errors

### Invalid PyPI token / 403

- Confirm the token is an **API Token** (not username/password) and its scope covers the target project.
- Inject via environment variables instead of writing into config:

```bash
export TWINE_PASSWORD=pypi-xxxxxxxx
autoship upload --target pypi
```

### Docker Registry 401

```bash
docker login ghcr.io
# or
docker login registry.hub.docker.com
```

`upload --target docker` relies on a prior local `docker login`.

## Language Switching Not Taking Effect

### `--lang` has no effect

```bash
autoship --lang en <command>
```

If output is still in Chinese, check:

1. Whether `locale` is set in `.autoship.toml` — config takes precedence over methods other than the CLI flag;
2. Whether your installed version supports the language (run `autoship --version` and cross-check the release notes);
3. The language switch on the docs site is routed by the i18n plugin and is independent of the CLI output language.

See [FAQ](faq.md) "How do I switch languages?".

## Still Stuck

- Run `autoship doctor` and include its output;
- See [Known Issues](known-issues.md);
- Open an issue: [GitHub Issues](https://github.com/MS33834/autoship-cli/issues).
