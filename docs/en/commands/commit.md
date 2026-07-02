---
title: commit
---
# commit

Generate a commit message and commit staged/unstaged changes.

## Syntax

```bash
autoship commit [OPTIONS]
```

## Arguments

`commit` does not accept positional arguments.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-m` | `--message TEXT` | - | Use the given commit message directly |
| - | `--edit / --no-edit` | `edit` | Open editor to refine the generated message |
| `-y` | `--yes` | `False` | Skip interactive confirmations and commit directly |

## Examples

Generate a message and open editor:

```bash
autoship commit
```

Use a specific message (no AI):

```bash
autoship commit -m "fix: resolve upload timeout"
```

Generate a message without editing:

```bash
autoship commit --no-edit
```

## Output Notes / Common Errors

- When `-m` is not provided, AutoShip uses a local model to generate a Conventional Commits style message from the diff and stats.
- The editor is validated against the configured `allowed_editors` list.
- Running outside a Git repository prints an error and suggests running `git init` first.

## Related Commands

- [verify](./verify.md) — Verify changes before committing
- [clean](./clean.md) — Clean code before committing
