---
title: Privacy Policy
---
# Privacy Policy

AutoShip adheres to the principles of **local-first** and **disabled by default**: unless you explicitly enable it, no usage data is collected, uploaded, or shared.

## 1. What Data We Collect

### 1.1 Telemetry Data (Disabled by Default)

When a user enables `[telemetry].enabled = true` in the configuration, AutoShip uploads anonymous usage statistics at the end of each command. The fields include:

| Field | Example | Description |
|---|---|---|
| `command` | `"clean"` | Command name |
| `exit_code` | `0` | Exit code |
| `duration_ms` | `123.45` | Command execution time (milliseconds) |
| `exception_type` | `"ConfigError"` | Exception type (if any) |
| `exception_lineno` | `42` | Line number where the exception occurred (if any) |
| `python_version` | `"3.12.4"` | Python major version |
| `platform` | `"Linux"` | Operating system family |
| `metrics_summary` | `{...}` | Global counter summary |

**The following is never collected:**

- File contents, diffs, source code
- File paths, working directory, hostname
- Command arguments, environment variables
- API keys, tokens, passwords, emails, and other credentials
- Usernames or other personally identifiable information (PII)

All telemetry records pass through a PII filter before being written to local logs or sent remotely; sensitive values such as paths, keys, and emails are replaced with `<path>` or `<redacted>`.

For more detailed telemetry configuration, batch sending, and endpoint security rules, see [docs/telemetry.md](telemetry.md).

### 1.2 Audit Logs (Enabled Locally by Default)

AutoShip writes structured audit logs locally by default for security investigation and compliance auditing. Audit logs include:

- Command invocation events and exit status
- Configuration changes and plugin operations
- Model call requests (redacted)
- SIEM forwarding records (if enabled)

Audit logs are also redacted; sensitive key-values and common token patterns are replaced with `***`.

## 2. Data Storage Locations

| Data Type | Default Path | Permissions |
|---|---|---|
| Telemetry local log | `~/.autoship/telemetry.logl` | Owner read/write |
| Audit log | `~/.autoship/logs/audit.{YYYY-MM-DD}.jsonl` | Directory `0o700`, file `0o600` |
| Configuration & cache | `~/.autoship/` or project root | Follows the principle of least privilege |

## 3. Data Retention & Cleanup

### 3.1 Telemetry Local Log

The telemetry local log is in JSON Lines format and **is not automatically rotated or cleaned up**. Users can delete it manually at any time:

```bash
rm ~/.autoship/telemetry.logl
```

### 3.2 Audit Logs

Audit logs are retained for **30 days** by default and can be adjusted via configuration:

```toml
[audit]
retention_days = 30
```

Run the following command to clean up expired logs:

```bash
autoship audit cleanup
```

The cleanup logic deletes `audit.*.jsonl` files whose `mtime` is older than `retention_days` days.

## 4. How to Enable or Disable Telemetry

### Command Line

```bash
# Enable telemetry
autoship config telemetry --enable

# Disable telemetry
autoship config telemetry --disable

# View current status
autoship config telemetry --status
```

### Configuration File

In `.autoship.toml`:

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

The legacy `telemetry_enabled = false` is still compatible and is automatically migrated to `[telemetry].enabled` at startup.

## 5. Remote Endpoint Security

- Only `https://` endpoints are accepted.
- By default, sending is only allowed to `telemetry.autoship.dev`.
- To send to other domains, both of the following must be met:
  - Set `allow_untrusted_endpoint = true` in the configuration file;
  - Or set the environment variable `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1`.
- The request timeout defaults to 5 seconds, with a maximum of 30 seconds.

## 6. Your Rights

- **Right to be informed**: All collected fields are publicly documented here and in [docs/telemetry.md](telemetry.md).
- **Right to control**: Telemetry is disabled by default; the user has full control and can enable or disable it at any time.
- **Right to review**: Local telemetry and audit logs are stored in plaintext JSON Lines and can be viewed directly by the user.
- **Right to deletion**: Manually deleting local log files clears all locally collected data.

## 7. Contact Us

For privacy-related questions, please contact us via:

- GitHub Issues: [https://github.com/MS33834/autoship-cli/issues](https://github.com/MS33834/autoship-cli/issues)
- Email: team@autoship.dev
