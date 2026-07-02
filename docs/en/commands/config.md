---
title: config
---
# config

Inspect and manage AutoShip configuration.

## Syntax

```bash
autoship config [OPTIONS] COMMAND [ARGS]...
```

## Arguments

`config` does not accept positional arguments; use subcommands.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--help` | - | Show help and exit |

## Subcommands

### config list

Show the effective configuration (sensitive values are redacted).

```bash
autoship config list [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | Output as JSON |

### config get

Get a single configuration value.

```bash
autoship config get [OPTIONS] KEY
```

| Name | Required | Description |
|---|---|---|
| `key` | Yes | Dotted configuration key, e.g. `model.default_tier` |

### config telemetry

Enable, disable, or view telemetry setting.

```bash
autoship config telemetry [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--enable` | `False` | Enable telemetry |
| - | `--disable` | `False` | Disable telemetry |
| - | `--status` | `False` | Show current telemetry status |

## Examples

List effective configuration:

```bash
autoship config list
```

View as JSON:

```bash
autoship config list --json
```

Get a single value:

```bash
autoship config get model.default_tier
```

Check telemetry status:

```bash
autoship config telemetry --status
```

Enable telemetry:

```bash
autoship config telemetry --enable
```

Disable telemetry:

```bash
autoship config telemetry --disable
```

## Output Notes / Common Errors

- `config list` redacts sensitive values such as API keys.
- Telemetry is disabled by default; no anonymous usage data is sent until explicitly enabled.
- Configuration can be overridden via `.autoship.toml`, environment variables (allowlist only), and CLI options.

## Related Commands

- [init](./init.md) — Initialize the configuration file
- [doctor](./doctor.md) — Check configuration and environment
