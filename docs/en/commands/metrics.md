---
title: metrics
---
# metrics

Inspect runtime metrics.

## Syntax

```bash
autoship metrics [OPTIONS] COMMAND [ARGS]...
```

## Arguments

`metrics` does not accept positional arguments; use subcommands.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--help` | - | Show help and exit |

## Subcommands

### metrics show

Display collected runtime metrics.

```bash
autoship metrics show [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | Output metrics as JSON |
| - | `--reset` | `False` | Reset metrics after displaying |

### metrics export

Export collected metrics to a JSON file.

```bash
autoship metrics export [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-o` | `--output PATH` | `~/.autoship/metrics.json` | Path to write the metrics JSON file |
| - | `--reset` | `False` | Reset metrics after exporting |

## Examples

Show metrics:

```bash
autoship metrics show
```

Show metrics as JSON:

```bash
autoship metrics show --json
```

Export to the default path:

```bash
autoship metrics export
```

Export to a specific path and reset metrics:

```bash
autoship metrics export --output ./metrics.json --reset
```

## Output Notes / Common Errors

- Metrics are collected locally and never uploaded unless telemetry is explicitly enabled.
- Use `--reset` to clear metrics after inspection.

## Related Commands

- [config](./config.md) — Configure telemetry
- [audit](./audit.md) — Export audit logs
