# Plugin Publishing Guide

This document explains how to submit a plugin to the official AutoShip plugin store.

## 1. Publishing Process Overview

1. Develop the plugin using [examples/custom-plugin](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin) as a template.
2. Complete local testing and make sure it passes at least `ruff check`, `pytest`, and AutoShip's `plugin verify`.
3. Generate a sha256 checksum for the plugin package, and optionally generate a PGP signature.
4. Publish the package to PyPI (or another pip-installable location such as a GitHub Release).
5. Submit a PR to this repository adding a new plugin entry to `registry/plugins.json`.
6. After maintainers review and merge it, the plugin automatically appears in the [Plugin Registry Web UI](https://ms33834.github.io/autoship-cli/registry/).

## 2. Metadata Format

Each plugin entry must be a JSON object with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Unique plugin identifier; only lowercase letters, digits, and hyphens are allowed. |
| `package` | string | Yes | pip install package name, e.g. `autoship-commit-sign`. |
| `module` | string | Yes | Python import path, e.g. `autoship_commit_sign.plugin`. |
| `version` | string | Yes | Semantic version number, e.g. `1.2.3`. |
| `description` | string | Yes | One-sentence description. |
| `trust_level` | string | Yes | `builtin` / `verified` / `community` / `untrusted`. |
| `entry_point` | string | Yes | Plugin entry point, e.g. `autoship_commit_sign.plugin:CommitSignPlugin`. |
| `hooks` | string[] | Yes | Supported hooks, e.g. `["pre_commit", "post_commit"]`. |
| `publisher` | object | Yes | `{ id, verified, url }`; `verified` requires admin confirmation. |
| `maintainer` | string | Yes | Maintainer name and contact email. |
| `license` | string | Yes | SPDX license identifier. |
| `sha256` | string | Recommended | sha256 checksum of the published package (wheel). Required for `verified` plugins. |
| `signature` | string | Recommended | base64-encoded signature of the sha256 using AutoShip's official private key. Required for `verified` plugins. |
| `permissions` | object | Yes | `{ filesystem, network, shell, git, env }`, declaring the permissions the plugin requires. |
| `categories` | string[] | Yes | Category tags, e.g. `["security", "git"]`. |
| `tags` | string[] | No | Search keywords. |
| `homepage` | string | Recommended | Plugin homepage URL. |
| `source_url` | string | Recommended | Source repository URL. |
| `downloads` | integer | No | Download count, maintained by the registry. |
| `rating` | object | No | `{ score, count }`, maintained by the registry. |
| `audit_status` | string | Yes | `pending` / `approved` / `rejected`; new submissions are `pending` and updated by admins after review. |

Full example:

```json
{
  "name": "commit-sign",
  "package": "autoship-commit-sign",
  "module": "autoship_commit_sign.plugin",
  "version": "1.0.0",
  "description": "Automatically adds a signature to generated commits.",
  "trust_level": "verified",
  "entry_point": "autoship_commit_sign.plugin:CommitSignPlugin",
  "hooks": ["pre_commit"],
  "publisher": {
    "id": "alice-chen",
    "verified": true,
    "url": "https://github.com/alice-chen"
  },
  "maintainer": "Alice Chen <alice@example.com>",
  "license": "MIT",
  "sha256": "a3f5c8e2b4d6f7a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5",
  "signature": "base64-encoded-pgp-signature",
  "permissions": {
    "filesystem": "read-only",
    "network": false,
    "shell": false,
    "git": true,
    "env": []
  },
  "categories": ["security", "git"],
  "tags": ["gpg", "sign", "commit"],
  "downloads": 0,
  "rating": { "score": 0.0, "count": 0 },
  "homepage": "https://github.com/example/autoship-commit-sign",
  "source_url": "https://github.com/example/autoship-commit-sign",
  "audit_status": "approved"
}
```

## 3. Checksum & Signature Requirements

### 3.1 Computing sha256

```bash
python -m build --wheel
sha256sum dist/autoship_commit_sign-1.0.0-py3-none-any.whl
```

Write the resulting 64-character hexadecimal string into the `sha256` field of `registry/plugins.json`.

### 3.2 Generating a Signature (verified plugins)

Only plugins with `trust_level: verified` require a signature. Admins sign the sha256 string with AutoShip's official PGP private key:

```bash
echo -n "<sha256-hex>" | gpg --armor --detach-sign --output signature.asc
# Write the base64-encoded signature content into registry/plugins.json
base64 -w 0 signature.asc
```

If the plugin does not apply for the `verified` level, keep `trust_level: community` and leave `sha256`/`signature` empty.

## 4. Verified Publisher Certification Process

The `verified` trust level identifies publishers and plugins reviewed by the AutoShip team. The application process is as follows:

### 4.1 Publisher Eligibility

Applicants must meet the following requirements:

- Maintain the plugin under a real identity or an active organization account.
- The plugin source repository is public and has been continuously maintained for at least 3 months or has released 2 or more versions.
- No history of serious security incidents or malicious behavior.

### 4.2 Submitting a Certification Application

Create an issue on GitHub using the **Verified Publisher Application** template, providing:

- Publisher ID (GitHub username or organization name) and homepage URL.
- A list of plugins already published or planned for maintenance.
- Contact information (public email or organization email).

### 4.3 Review Criteria

Maintainers review against the following criteria:

| Dimension | Requirement |
|---|---|
| Identity authenticity | Publisher identity is verifiable; homepage or organization profile is complete. |
| Plugin quality | Code passes `ruff check` and `pytest`; documentation and examples are complete. |
| Security compliance | Permission declarations are consistent with actual behavior; no excessive `network`/`shell` requests. |
| Continuous maintenance | Active commits or version releases in the last 3 months. |

### 4.4 Certification Result

- If approved: The publisher's information is recorded in `registry/publishers.json`, and their plugins may be marked with `publisher.verified = true`.
- If not approved: A reply is posted on the issue explaining the reason; you may reapply after supplementing the materials.
- Revocation: If the publisher subsequently has a security incident, stops maintaining for a long time, or provides false information, maintainers may revoke their `verified` status.

## 5. PR Template

When submitting a plugin to `registry/plugins.json`, please fill in the following in the PR description:

```markdown
## Plugin Submission

- **Plugin name**:
- **PyPI package name**:
- **Source URL**:
- **Requested trust level**: community / verified
- **sha256 of wheel**:
- **Signature** (if verified):

## Checklist

- [ ] The plugin source repository includes a `README.md`, an open-source license, and usage examples.
- [ ] The plugin passes at least `pytest` and `ruff check`.
- [ ] Installation has been verified with `autoship plugin verify <package>`.
- [ ] `permissions` have been filled in, and the permission scope does not exceed what the plugin actually needs.
- [ ] The sha256 checksum of the wheel has been provided (verified plugins also need a signature).
- [ ] I have read and agree to the [Privacy Policy](./privacy.md).
```

## 6. Review & Listing

1. Automated checks: CI validates the JSON schema, sha256 format, and required fields.
2. Security review: Maintainers examine high-sensitivity declarations such as `permissions`, `network`, and `shell`.
3. Experience review: Confirm that documentation, error messages, and usage examples are complete.
4. After merge: registry-web is deployed automatically, and users can find the plugin via `autoship plugin search <name>`.

## 7. Updates & Delisting

- **Version updates**: Submit a new PR updating `version`, `sha256`, and `signature`.
- **Delisting a plugin**: Change `audit_status` to `rejected` and explain the reason; plugins with serious security issues are removed from the registry.

## 8. Related Resources

- [Plugin Development Example](https://github.com/MS33834/autoship-cli/tree/main/examples/custom-plugin)
- [Plugin Registry Schema](https://github.com/MS33834/autoship-cli/blob/main/registry/schema.json)
- [Plugin Registry Web UI](https://ms33834.github.io/autoship-cli/registry/)
