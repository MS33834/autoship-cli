# Security Policy

## Supported Versions

| Version | Support Status |
|------|----------|
| 1.0.x | Current stable release; accepts security reports and prioritizes fixes |
| 0.2.x | No longer maintained |
| 0.1.x | No longer maintained |

Security fixes are backported to the latest stable major version. Pre-release versions (alpha/beta/rc) only receive fixes in the latest RC.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately via the following method instead of opening a public issue:

- Email: security@autoship.dev

Please include in your report:

- A description of the vulnerability and its impact scope
- Reproduction steps or a minimal reproduction example
- Affected versions
- Possible fix suggestions (if any)

We commit to acknowledging receipt within 5 business days and will fix and release an update as soon as possible after assessment.

## Security Design

AutoShip-CLI adopts the following security measures:

- **Local-first**: Uses local models and local toolchains by default to avoid uploading code to the cloud.
- **Credential management**: Sensitive information is not written to logs; using environment variables or the system keyring is recommended.
- **Plugin sandbox**: Plugins run through the hook mechanism, following the principle of least privilege.
- **Audit logs**: Key operations are recorded in audit logs for traceability.
- **Security scanning**: CI integrates bandit and pip-audit to continuously detect code and dependency vulnerabilities.

## Known Limitations

- Local model communication uses HTTP (such as Ollama's default port); please ensure the runtime environment is trusted.
- Plugins can execute system commands; please review the source when installing third-party plugins.

## Security Audit History

### 2026-06-19 Internal Security Review (before v1.0.0 release)

| Check Item | Tool/Method | Result |
|---|---|---|
| Static Application Security Testing (SAST) | bandit | No High/Medium issues |
| Dependency vulnerability scanning | pip-audit | No known unfixed vulnerabilities |
| Secret leak detection | gitleaks (CI) | No historical secret leaks found |
| Sensitive field redaction | Unit tests + manual review | Audit logs, telemetry, and error output are redacted |
| Plugin permission model | Code review | Permission declarations are minimized; high-risk operations require user confirmation |
| Path traversal & file permissions | Unit tests + fuzz testing | Fixed and regression tested |
| Supply chain security | wheel sha256 + PGP signature | Verified plugins are strictly validated |

### Red Team / Third-Party Penetration Testing

- Plan: Commission an external security team to conduct a full penetration test before v1.1.0.
- Current: Internal red team review is complete; no remotely exploitable high-severity vulnerabilities found.

## Historical Security Advisories

No disclosed security vulnerabilities as of 2026-06-22.
