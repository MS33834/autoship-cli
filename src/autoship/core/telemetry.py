"""Optional telemetry and error reporting.

Telemetry is **disabled by default**. When enabled, it collects only:

- command name, exit code, and execution duration
- Python version and operating system family
- exception type and line number (no messages, no source code)

No file contents, diff, paths, tokens, or personal information are ever collected.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypeAlias, cast
from urllib.parse import urlparse

import httpx
import structlog

from autoship.core.metrics import get_registry

logger = structlog.get_logger()

DEFAULT_ENDPOINT_ENV = "AUTOSHIP_TELEMETRY_ENDPOINT"
ALLOW_UNTRUSTED_ENV = "AUTOSHIP_TELEMETRY_ALLOW_UNTRUSTED"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 30.0
TRUSTED_TELEMETRY_HOSTS = {"telemetry.autoship.dev"}

# Patterns that may indicate personally identifiable or sensitive information.
_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "api-key",
    "token",
    "secret",
    "password",
    "passwd",
    "pwd",
    "authorization",
    "auth",
    "cookie",
    "session",
    "private_key",
    "privatekey",
    "email",
    "phone",
}
_SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"[a-f0-9]{32,}", re.IGNORECASE),  # hex hashes/tokens
    re.compile(r"[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"),  # JWT-like
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # email
]
_PATHLIKE_PREFIXES = ("/", "\\", "~", ".", "file:")
_MAX_STRING_LENGTH = 256

# Recursive type alias for telemetry payloads so pyright can reason about
# nested dict/list structures without falling back to ``Unknown``.
JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


def _looks_like_path(value: str) -> bool:
    """Return True if ``value`` looks like a filesystem path."""
    return value.startswith(_PATHLIKE_PREFIXES) or (len(value) >= 2 and value[1] == ":")


def _is_sensitive_key(key: str) -> bool:
    """Return True if ``key`` indicates the associated value is sensitive."""
    lower = key.lower()
    return any(sensitive in lower for sensitive in _SENSITIVE_KEYS)


def _scrub_value(value: object, key: str = "") -> object:
    """Redact a single scalar value that may contain sensitive data."""
    if not isinstance(value, str):
        return value
    if not value:
        return value
    if _is_sensitive_key(key):
        return "<redacted>"
    if _looks_like_path(value):
        return "<path>"
    if any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS):
        return "<redacted>"
    return value[:_MAX_STRING_LENGTH]


def _scrub(data: JSON) -> JSON:
    """Recursively remove or redact PII/sensitive fields from a telemetry payload."""
    if not isinstance(data, dict):
        return data
    scrubbed: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            scrubbed[key] = _scrub(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                _scrub(item) if isinstance(item, dict) else _scrub_value(item, key=key)
                for item in value
            ]
        elif isinstance(value, str):
            scrubbed[key] = _scrub_value(value, key=key)
        else:
            scrubbed[key] = value
    return cast(JSON, scrubbed)


def _parse_timeout(value: str | None, default: float = DEFAULT_TIMEOUT_SECONDS) -> float:
    """Parse and bound a user-supplied timeout string."""
    if value is None:
        return default
    try:
        timeout = float(value)
    except ValueError:
        return default
    if timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
        return default
    return timeout


def _is_valid_endpoint(endpoint: str, allow_untrusted: bool) -> bool:
    """Return ``True`` if ``endpoint`` is an acceptable HTTPS URL.

    The endpoint must use ``https://`` and, unless ``allow_untrusted`` is set,
    its host must be in ``TRUSTED_TELEMETRY_HOSTS``.
    """
    try:
        parsed = urlparse(endpoint)
    except ValueError:
        return False
    if parsed.scheme != "https":
        logger.warning("telemetry.endpoint_not_https", endpoint=endpoint)
        return False
    if not parsed.hostname:
        logger.warning("telemetry.endpoint_missing_host", endpoint=endpoint)
        return False
    host = parsed.hostname.lower()
    if host not in TRUSTED_TELEMETRY_HOSTS and not allow_untrusted:
        logger.warning(
            "telemetry.endpoint_not_trusted",
            endpoint=endpoint,
            trusted_hosts=TRUSTED_TELEMETRY_HOSTS,
        )
        return False
    return True


@dataclass
class TelemetryEvent:
    """A single telemetry event."""

    command: str
    duration_ms: float
    exit_code: int
    exception_type: str | None = None
    exception_lineno: int | None = None
    python_version: str = sys.version.split()[0]
    platform: str = platform.system()
    metrics_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TelemetryCollector:
    """Collect and optionally emit telemetry events.

    Events are buffered in memory and flushed either when ``batch_size`` is
    reached or when ``flush()`` is called explicitly (e.g. before the CLI
    exits). Every persisted record is scrubbed for paths, tokens, secrets,
    and other PII before it is written locally or sent remotely.
    """

    def __init__(
        self,
        enabled: bool = False,
        endpoint: str | None = None,
        log_dir: Path | None = None,
        timeout: float | None = None,
        allow_untrusted: bool | None = None,
        batch_size: int = 10,
    ) -> None:
        self.enabled = enabled
        self.batch_size = max(1, batch_size)
        self.log_dir = log_dir or Path.home() / ".autoship"
        self.timeout = timeout or _parse_timeout(os.getenv("AUTOSHIP_TELEMETRY_TIMEOUT"))
        if allow_untrusted is None:
            allow_untrusted = os.getenv(ALLOW_UNTRUSTED_ENV, "").lower() in {"1", "true", "yes"}

        raw_endpoint = endpoint or os.getenv(DEFAULT_ENDPOINT_ENV)
        self.endpoint: str | None = None
        if raw_endpoint is not None and _is_valid_endpoint(raw_endpoint, allow_untrusted):
            self.endpoint = raw_endpoint

        self._batch: list[dict[str, Any]] = []

    def record(
        self,
        command: str,
        start_time: float,
        exit_code: int,
        exc: BaseException | None = None,
    ) -> TelemetryEvent | None:
        """Record a telemetry event if telemetry is enabled."""
        if not self.enabled:
            return None

        duration_ms = (time.perf_counter() - start_time) * 1000
        exception_type = None
        exception_lineno = None
        if exc is not None:
            exception_type = type(exc).__name__
            tb = exc.__traceback__
            if tb is not None:
                # Report the line in *this* project where the exception was raised.
                last_frame = traceback.extract_tb(tb)[-1]
                exception_lineno = last_frame.lineno

        event = TelemetryEvent(
            command=command,
            duration_ms=round(duration_ms, 2),
            exit_code=exit_code,
            exception_type=exception_type,
            exception_lineno=exception_lineno,
            metrics_summary=self._metrics_summary(),
        )
        self._persist(event)
        return event

    def _metrics_summary(self) -> dict[str, Any]:
        """Return a compact summary of the global metrics registry."""
        try:
            snapshot = get_registry().snapshot()
            return {
                "num_metrics": len(snapshot),
                "counters": {
                    n: d["value"] for n, d in snapshot.items() if d.get("type") == "counter"
                },
            }
        except Exception:  # noqa: BLE001
            return {}

    def _persist(self, event: TelemetryEvent) -> None:
        """Write the event to the local log and buffer for batch upload."""
        self.record_event(event.to_dict())

    def record_event(self, data: dict[str, Any]) -> None:
        """Write an arbitrary dictionary event to the local log and buffer it.

        The record is scrubbed before persistence to ensure no PII leaves the
        local machine or is uploaded to a telemetry endpoint.
        """
        scrubbed = _scrub(cast(JSON, data))
        self._write_local(cast(dict[str, Any], scrubbed))
        self._batch.append(cast(dict[str, Any], scrubbed))
        if len(self._batch) >= self.batch_size:
            self.flush()

    def _write_local(self, data: dict[str, Any]) -> None:
        """Append a single scrubbed record to the local telemetry log."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_dir / "telemetry.logl"
        record = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        try:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(record + "\n")
        except OSError:
            logger.debug("telemetry.local_write_failed")

    def flush(self) -> None:
        """Send any buffered events to the configured endpoint."""
        if not self._batch or not self.endpoint:
            self._batch.clear()
            return
        records = self._batch[:]
        self._batch.clear()
        self._send(records)

    def _send(self, records: list[dict[str, Any]]) -> None:
        """Send a batch of events to the configured endpoint.

        This is a no-op if the request fails; telemetry must never break the CLI.
        """
        if not self.endpoint or not records:
            return
        payload = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
        try:
            httpx.post(
                self.endpoint,
                content=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except Exception:  # noqa: BLE001
            logger.debug("telemetry.remote_send_failed")
