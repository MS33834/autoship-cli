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
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
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
    """Collect and optionally emit telemetry events."""

    def __init__(
        self,
        enabled: bool = False,
        endpoint: str | None = None,
        log_dir: Path | None = None,
        timeout: float | None = None,
        allow_untrusted: bool | None = None,
    ) -> None:
        self.enabled = enabled
        self.log_dir = log_dir or Path.home() / ".autoship"
        self.timeout = timeout or _parse_timeout(os.getenv("AUTOSHIP_TELEMETRY_TIMEOUT"))
        if allow_untrusted is None:
            allow_untrusted = os.getenv(ALLOW_UNTRUSTED_ENV, "").lower() in {"1", "true", "yes"}

        raw_endpoint = endpoint or os.getenv(DEFAULT_ENDPOINT_ENV)
        if raw_endpoint is not None and _is_valid_endpoint(raw_endpoint, allow_untrusted):
            self.endpoint = raw_endpoint
        else:
            self.endpoint = None

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
        """Write the event to the local log and optionally send it."""
        self.record_event(event.to_dict())

    def record_event(self, data: dict[str, Any]) -> None:
        """Write an arbitrary dictionary event to the local log and optionally send it."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_dir / "telemetry.logl"
        record = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        try:
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(record + "\n")
        except OSError:
            logger.debug("telemetry.local_write_failed")

        if self.endpoint:
            self._send(record)

    def _send(self, record: str) -> None:
        """Send the event to the configured endpoint.

        This is a no-op if the request fails; telemetry must never break the CLI.
        """
        if not self.endpoint:
            return
        try:
            httpx.post(
                self.endpoint,
                content=record,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
        except Exception:  # noqa: BLE001
            logger.debug("telemetry.remote_send_failed")
