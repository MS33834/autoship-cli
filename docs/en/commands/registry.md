---
title: registry
---
# registry

Browse the plugin registry and sync the index.

## Syntax

```bash
autoship registry [OPTIONS] COMMAND [ARGS]...
```

## Arguments

`registry` does not accept positional arguments; use subcommands.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--help` | - | Show help and exit |

## Subcommands

### registry list

Show the registry analytics dashboard. `list` is an alias for `dashboard`.

```bash
autoship registry list [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | Number of plugins to show in top lists |

### registry dashboard

Show the registry analytics dashboard.

```bash
autoship registry dashboard [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--top INTEGER` | `5` | Number of plugins to show in top lists |

### registry sync

Sync the plugin registry index from the remote source.

```bash
autoship registry sync [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/registry/plugins.json` | Output path for the synced index |
| `-f` | `--force` | `False` | Force overwrite local cache |
| - | `--dry-run` | `False` | Preview changes without writing |

## Examples

Open the registry dashboard:

```bash
autoship registry list
```

Show top 10 plugins:

```bash
autoship registry list --top 10
```

Sync the registry index:

```bash
autoship registry sync
```

Force re-sync:

```bash
autoship registry sync --force
```

Preview sync:

```bash
autoship registry sync --dry-run
```

## Output Notes / Common Errors

- The default registry URL points to the official GitHub-hosted index.
- The signature and hash of the downloaded index are verified when a public key is configured.

## Related Commands

- [plugin](./plugin.md) — Install and manage plugins
- [doctor](./doctor.md) — Check environment
