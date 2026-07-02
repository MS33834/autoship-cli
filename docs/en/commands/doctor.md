---
title: doctor
---
# doctor

Diagnose the AutoShip environment and dependencies.

## Syntax

```bash
autoship doctor [OPTIONS]
```

## Arguments

`doctor` does not accept positional arguments.

## Options

| Short | Long | Default | Description |
|:-:|:-:|:-:|---|
| - | `--json` | `False` | Output report as JSON |
| - | `--fail-on-error` | `False` | Exit with non-zero code when errors are present |

## Examples

Run a health check:

```bash
autoship doctor
```

Structured output for CI:

```bash
autoship doctor --json
```

Fail the pipeline on errors:

```bash
autoship doctor --fail-on-error
```

## Output Notes / Common Errors

- Checks include Python version, Git configuration, model backend connectivity, clean toolchain, plugin external dependencies, and audit/telemetry directory permissions.
- Results are graded OK / WARNING / ERROR. A missing local model backend is reported as WARNING and does not affect non-AI commands.
- doctor respects `project_type` to skip irrelevant tool checks. Non-Python projects skip `autoflake` / `black` checks, avoiding unrelated ERROR or WARNING items.

## Related Commands

- [config](./config.md) — Inspect configuration
- [plugin](./plugin.md) — Manage plugins
