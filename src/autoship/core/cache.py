"""Local disk cache for model responses and web search results.

The cache stores JSON payloads keyed by the SHA256 hash of the caller-provided
key. Writes are atomic (write-temp-then-rename) and protected by per-key file
locks on POSIX systems, making the cache safe to use from multiple threads and
processes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_has_fcntl = importlib.util.find_spec("fcntl") is not None


class DiskCache:
    """Thread/process-safe file-based cache keyed by SHA256 hashes.

    Args:
        cache_dir: Directory where cache entries are stored. Defaults to
            ``~/.autoship/cache``.
        default_ttl: Default time-to-live for cache entries, in seconds.
    """

    def __init__(self, cache_dir: Path | None = None, default_ttl: int = 3600) -> None:
        self.cache_dir = cache_dir or Path.home() / ".autoship" / "cache"
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @staticmethod
    def _hash_key(key: str) -> str:
        """Return the SHA256 hex digest of ``key``."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        """Return the filesystem path for ``key``."""
        return self.cache_dir / f"{self._hash_key(key)}.cache"

    def _lock_path(self, key: str) -> Path:
        """Return the advisory lock file path for ``key``."""
        return self.cache_dir / f"{self._hash_key(key)}.lock"

    @contextmanager
    def _file_lock(self, key: str, *, exclusive: bool = True) -> Generator[None, None, None]:
        """Acquire an advisory file lock for ``key`` while in the context."""
        lock_path = self._lock_path(key)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
        try:
            if _has_fcntl:
                import fcntl  # pyright: ignore[reportMissingTypeStubs]

                operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
                fcntl.flock(fd, operation)
            yield
        finally:
            if _has_fcntl:
                import fcntl  # pyright: ignore[reportMissingTypeStubs]

                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def get(self, key: str) -> Any | None:
        """Return the cached value for ``key`` or ``None`` if missing/expired."""
        path = self._cache_path(key)
        with self._lock, self._file_lock(key, exclusive=False):
            if not path.exists():
                return None
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None

            expires = data.get("expires")
            if expires is not None and time.time() > expires:
                return None
            return data.get("value")

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store ``value`` under ``key`` with an optional TTL override."""
        path = self._cache_path(key)
        with self._lock, self._file_lock(key, exclusive=True):
            expires = time.time() + (ttl if ttl is not None else self.default_ttl)
            payload = json.dumps({"expires": expires, "value": value})
            tmp_path = path.with_suffix(".tmp")
            tmp_path.write_text(payload, encoding="utf-8")
            tmp_path.replace(path)

    def invalidate(self, key: str) -> None:
        """Remove the entry for ``key`` if it exists."""
        path = self._cache_path(key)
        with self._lock, self._file_lock(key, exclusive=True):
            if path.exists():
                path.unlink()

    def clear(self) -> None:
        """Remove all cache entries and advisory lock files."""
        with self._lock:
            for entry in self.cache_dir.glob("*.cache"):
                entry.unlink(missing_ok=True)
            for entry in self.cache_dir.glob("*.lock"):
                entry.unlink(missing_ok=True)
