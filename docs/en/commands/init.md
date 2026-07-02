---
title: init
---
# init

Initialize an AutoShip configuration file for the current project.

## Syntax

```bash
autoship init [OPTIONS]
```

## Arguments

`init` does not accept positional arguments.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--type TEXT` | - | Override project type detection |
| `-o` | `--output PATH` | `.autoship.toml` | Config file output path |
| `-y` | `--yes` | `False` | Skip interactive confirmations |

## Examples

Initialize in the current directory:

```bash
autoship init
```

Force a specific project type:

```bash
autoship init --type python
```

Write the config to a custom path:

```bash
autoship init -o autoship.toml
```

Skip confirmations in CI:

```bash
autoship init --yes
```

## Output Notes / Common Errors

- Detects project type and hardware capabilities, then recommends a suitable model tier.
- If the target file already exists, `--yes` will overwrite it without prompting.

## Related Commands

- [config](./config.md) — Inspect and manage configuration
- [doctor](./doctor.md) — Check environment and configuration
