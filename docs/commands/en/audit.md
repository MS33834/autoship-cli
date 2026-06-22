# audit

Export or clean up audit logs.

## Syntax

```bash
autoship audit [OPTIONS] COMMAND [ARGS]...
```

## Arguments

`audit` does not accept positional arguments; use subcommands.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--help` | - | Show help and exit |

## Subcommands

### audit export

Export audit logs to a JSON Lines file.

```bash
autoship audit export [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| `-s` | `--since TEXT` | - | Export records after this time (ISO date or `1d`/`7d`/`30d`) |
| `-o` | `--output PATH` | - | Output file path |

### audit cleanup

Remove audit log files older than the retention period.

```bash
autoship audit cleanup [OPTIONS]
```

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--retention-days INTEGER` | - | Retention period in days |
| - | `--dry-run` | `False` | Preview actions |

## Examples

Export the last 30 days:

```bash
autoship audit export --since 30d
```

Export to a specific file:

```bash
autoship audit export --since 2025-01-01 --output ./audit.jsonl
```

Clean up logs older than 90 days:

```bash
autoship audit cleanup --retention-days 90
```

Preview cleanup:

```bash
autoship audit cleanup --retention-days 90 --dry-run
```

## Output Notes / Common Errors

- `--since` accepts ISO dates or relative durations such as `1d`, `7d`, `30d`.
- Audit logs are stored in `.autoship/audit/` under the project root by default.

## Related Commands

- [doctor](./doctor.md) — Check audit/telemetry directory permissions
- [config](./config.md) — Configure audit settings
