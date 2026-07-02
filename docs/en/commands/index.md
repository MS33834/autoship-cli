---
title: Command Reference
---
# Command Reference

AutoShip CLI commands follow a unified lifecycle: load configuration, invoke `pre_*` hooks, execute the command body, invoke `post_*` hooks, and record audit logs. This reference provides the full syntax, arguments, options, and examples for every command.

## Global Options

These options apply to all commands and are usually placed before the subcommand (e.g. `autoship --verbose init`):

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-v` | `--verbose` | `False` | Verbose output |
| `-n` | `--dry-run` | `False` | Preview actions without executing |
| `-y` | `--yes` | `False` | Skip interactive confirmations |
| `-c` | `--config PATH` | - | Path to configuration file |
| - | `--lang TEXT` | `auto` | Output language (`en`, `zh`, `ja`, `auto`) |
| - | `--install-completion` | - | Install shell completion |
| - | `--show-completion` | - | Show shell completion script |

View global options at any time:

```bash
autoship --help
autoship --lang en --help
```

## Command List

| Command | Description | Subcommands |
|---|---|---|
| [init](./init.md) | Initialize an AutoShip configuration file for the project | - |
| [clean](./clean.md) | Clean and format project code | - |
| [verify](./verify.md) | Run a verification command and capture errors for AI-assisted fixing | - |
| [fix](./fix.md) | Ask an LLM to propose a fix for the last verification failure | - |
| [commit](./commit.md) | Generate a commit message and commit changes | - |
| [upload](./upload.md) | Upload artifacts to a configured target | - |
| [plugin](./plugin.md) | Manage plugins | `list`, `search`, `info`, `install`, `uninstall`, `rate`, `stats`, `trust`, `update` |
| [doctor](./doctor.md) | Diagnose the AutoShip environment and dependencies | - |
| [audit](./audit.md) | Export or clean up audit logs | `export`, `cleanup` |
| [registry](./registry.md) | Browse the plugin registry and sync the index | `list`, `dashboard`, `sync` |
| [metrics](./metrics.md) | Inspect runtime metrics | `show`, `export` |
| [config](./config.md) | Inspect and manage AutoShip configuration | `list`, `get`, `telemetry` |

## Document Structure

- `index.md` (this page): global options and command index.
- `<command>.md`: standalone reference page for each command, including overview, syntax, arguments, options, examples, output notes, and related commands.
- Complex commands (`plugin`, `audit`, `registry`, `metrics`, `config`) include detailed subcommand sections.

## Contributing

Keep the command reference consistent with the actual CLI `--help` output. Before editing, run:

```bash
uv run python -m autoship <cmd> --help
```

When adding a new command, update the table on this page and the `mkdocs.yml` navigation.
