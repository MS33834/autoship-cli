---
title: verify
---
# verify

Run a verification command and capture errors for AI-assisted fixing.

## Syntax

```bash
autoship verify [OPTIONS] COMMAND
```

## Arguments

| Name | Required | Description |
|---|---|---|
| `command` | Yes | Command to run for verification, e.g. `pytest` |

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--fix` | `False` | Ask the model to suggest fixes on failure |

## Examples

Run pytest:

```bash
autoship verify pytest
```

Run a command with arguments (quote it):

```bash
autoship verify "pytest tests/unit"
```

Request AI fix suggestions on failure:

```bash
autoship verify pytest --fix
```

## Output Notes / Common Errors

- `--fix` triggers the `on_error` hook, collects `FixSuggestion`s, and prompts before applying patches.
- Failure summaries are saved in `.autoship/error/` with sensitive values redacted.

## Related Commands

- [fix](./fix.md) — Generate a fix for the last failure
- [clean](./clean.md) — Clean and format code
