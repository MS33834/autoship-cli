#!/usr/bin/env python3
"""Validate the AutoShip plugin registry index.

This script is used by the plugin_review GitHub Actions workflow to ensure
that every plugin entry in ``src/autoship/registry/plugins.json`` meets the
minimum metadata and trust requirements.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# SPDX identifiers commonly used by Python packages. Keeping the list small and
# explicit avoids pulling in extra dependencies in CI.
VALID_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "MPL-2.0",
    "ISC",
    "Unlicense",
    "0BSD",
}

TRUST_LEVELS = {"builtin", "verified", "community", "untrusted"}
REQUIRED_FIELDS = {"name", "package", "version", "description", "trust_level", "entry_point", "maintainer", "license", "publisher"}


def _error(message: str) -> None:
    print(f"ERROR: {message}")


def _warn(message: str) -> None:
    print(f"WARN: {message}")


def validate_version(version: str) -> bool:
    """Perform a loose PEP 440 / semver-like validation."""
    return bool(re.match(r"^\d+(\.\d+)*(?:[a-zA-Z]+\d+)?$", version))


def validate_plugin(plugin: dict, index: int, names: set[str]) -> int:
    """Validate a single plugin entry. Returns the number of errors."""
    errors = 0
    prefix = f"Plugin #{index}"

    missing = REQUIRED_FIELDS - set(plugin.keys())
    if missing:
        _error(f"{prefix} missing required fields: {sorted(missing)}")
        errors += 1

    name = plugin.get("name")
    if name:
        if name in names:
            _error(f"{prefix} duplicate plugin name: {name}")
            errors += 1
        names.add(name)
        prefix = f"Plugin '{name}'"

    trust_level = plugin.get("trust_level")
    if trust_level and trust_level not in TRUST_LEVELS:
        _error(f"{prefix} invalid trust_level: {trust_level}")
        errors += 1

    version = plugin.get("version", "")
    if version and not validate_version(version):
        _error(f"{prefix} invalid version: {version}")
        errors += 1

    license_id = plugin.get("license")
    if license_id and license_id not in VALID_LICENSES:
        _warn(f"{prefix} license '{license_id}' is not in the common SPDX allow-list")

    if trust_level == "verified" and not (plugin.get("sha256") or plugin.get("signature")):
        _error(f"{prefix} verified plugins must provide sha256 or signature")
        errors += 1

    for field in ("categories", "tags"):
        value = plugin.get(field)
        if value is not None and not isinstance(value, list):
            _error(f"{prefix} '{field}' must be a list")
            errors += 1

    rating = plugin.get("rating")
    if rating is not None and (
        not isinstance(rating, dict) or "score" not in rating or "count" not in rating
    ):
        _error(f"{prefix} 'rating' must be an object with 'score' and 'count'")
        errors += 1

    publisher = plugin.get("publisher")
    if publisher is not None:
        if not isinstance(publisher, dict):
            _error(f"{prefix} 'publisher' must be an object")
            errors += 1
        else:
            for key in ("id", "verified"):
                if key not in publisher:
                    _error(f"{prefix} 'publisher' missing required field '{key}'")
                    errors += 1

    return errors


def main() -> int:
    registry_path = Path(__file__).resolve().parents[1] / "src" / "autoship" / "registry" / "plugins.json"
    if not registry_path.exists():
        _error(f"Registry index not found: {registry_path}")
        return 1

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _error(f"Invalid JSON in {registry_path}: {exc}")
        return 1

    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        _error("'plugins' must be a list")
        return 1

    names: set[str] = set()
    total_errors = 0
    for idx, plugin in enumerate(plugins, start=1):
        if not isinstance(plugin, dict):
            _error(f"Plugin #{idx} is not an object")
            total_errors += 1
            continue
        total_errors += validate_plugin(plugin, idx, names)

    if total_errors:
        print(f"Validation failed with {total_errors} error(s).")
        return 1

    print(f"Validation passed for {len(plugins)} plugin(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
