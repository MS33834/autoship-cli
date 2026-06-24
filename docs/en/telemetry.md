# Telemetry & Privacy

AutoShip has telemetry **disabled by default**. Only after you explicitly enable it will anonymous usage statistics be collected and sent.

## What Data Is Collected

When telemetry is enabled, the following fields are uploaded at the end of each command:

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

All records written to local logs or sent remotely first pass through a PII filter; sensitive values such as paths, keys, and emails are replaced with `<path>` or `<redacted>`.

## How to Enable or Disable

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

Add the following to `.autoship.toml`:

```toml
[telemetry]
enabled = true
endpoint = "https://telemetry.autoship.dev/v1/events"
batch_size = 10
timeout = 5.0
allow_untrusted_endpoint = false
```

The legacy `telemetry_enabled = false` configuration is still compatible and is automatically migrated to `[telemetry].enabled` at startup.

## Remote Endpoint Security Rules

- Only `https://` endpoints are accepted.
- By default, sending is only allowed to `telemetry.autoship.dev`.
- To send to other domains, both of the following must be met:
  - Set `allow_untrusted_endpoint = true` in the configuration file;
  - Or set the environment variable `AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED=1`.
- The request timeout defaults to 5 seconds, with a maximum of 30 seconds.

## Batch Sending & Local Logs

Telemetry events are first written to the local `~/.autoship/telemetry.logl` and buffered in memory. When the buffer count reaches `batch_size` (default 10) or `flush()` is called before the CLI exits, they are sent in a single batch to the configured endpoint. A send failure does not affect normal CLI usage.

## Privacy Policy Summary

1. Disabled by default; the user has full control.
2. Data is anonymized and contains no PII.
3. All outbound telemetry uses HTTPS and is protected by domain validation.
4. Both local logs and remote data are redacted.
5. Users can opt out at any time via `autoship config telemetry --disable`.

To audit local telemetry content, view `~/.autoship/telemetry.logl` (JSON Lines format).
