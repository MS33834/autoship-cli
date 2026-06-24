"""Shared hashing and package-installer helpers."""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _in_virtualenv() -> bool:
    """Return True when the active interpreter is inside a virtual environment."""
    return hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix


def pip_cmd() -> list[str]:
    """Return the preferred package installer command (uv or pip).

    ``uv pip`` is used only when ``uv`` is available *and* the active interpreter
    is running inside a virtual environment, because ``uv pip install`` refuses
    to install into a non-virtual environment without ``--system``.
    """
    if shutil.which("uv") and _in_virtualenv():
        return ["uv", "pip"]
    return ["pip"]
