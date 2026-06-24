# Security Audit & Penetration Testing

This document records AutoShip-CLI's security audit process, tool configuration, and historical results, for reference by security teams, auditors, and advanced users.

## Continuous Security Scanning

The following security scans run on every commit and nightly build:

| Tool | Purpose | Trigger |
|---|---|---|
| [bandit](https://bandit.readthedocs.io/) | Python SAST | CI, nightly |
| [pip-audit](https://pypi.org/project/pip-audit/) | Dependency vulnerability scanning | CI, nightly |
| [gitleaks](https://gitleaks.io/) | Secret leak detection | CI, nightly |
| [ruff](https://docs.astral.sh/ruff/) | lint + some security rules | CI, pre-commit |
| Dependabot | Automatic dependency updates | Weekly |

## Pre-Release Security Audit Process

Before each major version release, the security team should perform the following audit:

### 1. Code Audit

- Review all code paths that handle external input (CLI arguments, configuration files, plugins, model responses).
- Confirm that path operations use `Path.resolve()` and are constrained to allowed ranges.
- Confirm that subprocess calls do not use `shell=True` unless explicitly authorized by the user.
- Check that sensitive data is redacted via `autoship.core.redaction` or equivalent logic.

### 2. Configuration & Credential Audit

- Confirm that default configuration disables telemetry and external model backends.
- Confirm that API key, token, and other fields support `${ENV_VAR}` injection.
- Verify that the default configuration file permission is `0o600`.

### 3. Plugin Security Audit

- Use `autoship plugin verify <package>` to check that third-party plugins' declared permissions match their actual behavior.
- Perform source code review on plugins applying for the `verified` level.
- Confirm that the `sandbox` restricts plugin file system access.

### 4. Dependency & Supply Chain Audit

- Run `uv run pip-audit --desc` and fix all `HIGH` level vulnerabilities.
- Check whether dependencies in `pyproject.toml` have unpinned versions or known issues.
- Confirm that release.yml uses Trusted Publishing or a least-privilege PyPI token.

### 5. Penetration Testing Checklist

| Test Item | Method | Expected Result |
|---|---|---|
| Path traversal | Construct arguments like `../../../etc/passwd` | Rejected or resolves to within the allowed directory |
| Command injection | Embed backticks and semicolons in commit messages / diffs | Not parsed or executed by the shell |
| SSRF | Configure a model backend pointing to an internal address | Follows user configuration but is untrusted by default |
| Sensitive information leak | Trigger an exception and check logs | No plaintext API keys, passwords, or tokens |
| Plugin privilege escalation | Install a plugin declaring low privileges but attempting high-privilege operations | Blocked by permission checks |
| Denial of service | 1000+ file project + extra-long diff | Completes within timeout without crashing |

## Historical Audit Results

### 2026-06-19 v1.0.0 Internal Security Review

- **Performed by**: AutoShip security team
- **Scope**: CLI, core library, built-in plugins, registry, CI/CD
- **Results**:
  - bandit: 0 High/Medium
  - pip-audit: 0 unfixed vulnerabilities
  - Path traversal and command injection tests: passed
  - Sensitive information leak tests: passed
  - Plugin permission tests: passed
- **Residual risks**:
  - Local model backends use HTTP by default; relies on the security of the user's environment.
  - Third-party community plugins have not undergone complete source code audits; users must judge for themselves.

### Planned External Audit

- **Target version**: v1.1.0
- **Performed by**: Third-party security firm / community red team
- **Scope**: Complete CLI attack surface, plugin system, supply chain
- **Deliverables**: Penetration test report, fix recommendations, public summary

## How to Report Security Issues

Please follow the process in [SECURITY.md](https://github.com/MS33834/autoship-cli/blob/main/SECURITY.md) and report privately via email.
