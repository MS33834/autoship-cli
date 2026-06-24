"""Shared hashing and package-installer helpers."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def pip_cmd() -> list[str]:
    """Return the preferred package installer command (uv or pip)."""
    if shutil.which("uv"):
        return ["uv", "pip"]
    return ["pip"]
