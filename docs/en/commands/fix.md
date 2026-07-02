---
title: fix
---
# fix

Ask an LLM to propose a fix for the last verification failure.

## Syntax

```bash
autoship fix [OPTIONS] [ERROR_FILE]
```

## Arguments

| Name | Required | Description |
|---|---|---|
| `error_file` | No | Path to error log; defaults to the last `verify` output |

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-y` | `--yes` | `False` | Skip confirmations |

## Examples

Fix the most recent failure:

```bash
autoship fix
```

Fix a specific error log:

```bash
autoship fix .autoship/error/last_error.txt
```

Apply suggestions without prompting:

```bash
autoship fix --yes
```

## Output Notes / Common Errors

- Only files inside the project root and with allowed extensions are sent to the model.
- Large files are skipped; the command lists which files are read.

## Related Commands

- [verify](./verify.md) — Run verification and capture errors
- [commit](./commit.md) — Commit the resulting changes
