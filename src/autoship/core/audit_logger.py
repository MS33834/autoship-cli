"""Structured audit logging for security and observability."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import httpx

from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")

# Common sensitive field names that should never be forwarded to a SIEM.
SENSITIVE_KEYS = frozenset(
    {
        "token",
        "api_key",
        "password",
        "secret",
        "siem_token",
        "key",
        "private",
        "credentials",
        "auth",
        "authorization",
        "access_token",
        "refresh_token",
    }
)


class AuditLogger:
    """Append-only JSONL audit logger with optional SIEM forwarding.

    Logs are written to ``~/.autoship/logs/audit.{YYYY-MM-DD}.jsonl``
    by default, or to ``config.audit_log_dir`` / ``config.audit.log_dir``
    when provided. Each command invocation shares a single ``trace_id``.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.trace_id = str(uuid.uuid4())
        log_dir = self._resolve_log_dir()
        self.log_dir = Path(log_dir)
        self._ensure_log_dir()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"audit.{today}.jsonl"
        self._context: dict[str, Any] = {}
        self._siem_client: httpx.Client | None = None
        if config.audit.siem_enabled and config.audit.siem_url:
            headers: dict[str, str] = {}
            if config.audit.siem_token:
                headers["Authorization"] = f"Bearer {config.audit.siem_token}"
            self._siem_client = httpx.Client(
                base_url=str(config.audit.siem_url),
                headers=headers,
                timeout=5.0,
            )

    def _resolve_log_dir(self) -> Path:
        """Return the configured or default audit log directory."""
        if self.config.audit_log_dir:
            return self.config.audit_log_dir
        if self.config.audit.log_dir:
            return self.config.audit.log_dir
        return Path.home() / ".autoship" / "logs"

    def _ensure_log_dir(self) -> None:
        """Create the log directory, tolerating permission errors."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning("Cannot create audit log directory %s: %s", self.log_dir, exc)

    def record(self, event: str, payload: dict[str, Any] | None = None) -> None:
        """Append a structured audit record.

        IO failures are logged but never propagated so that audit issues do
        not break user commands.
        """
        context = getattr(self, "_context", {})
        merged_payload = {**context, **(payload or {})}
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": self.trace_id,
            "event": event,
            "payload": self._redact(merged_payload),
        }
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError as exc:
            logger.warning("Failed to write audit record for %s: %s", event, exc)
        self._forward_to_siem(entry)

    def export(
        self,
        since: datetime | None = None,
        output: Path | None = None,
    ) -> Path:
        """Export audit records to a single JSON Lines file.

        If ``since`` is provided, only records with a timestamp greater than or
        equal to ``since`` are included. If ``output`` is not provided, a
        temporary file is created.
        """
        if output is None:
            output = self.log_dir / f"audit.export.{self.trace_id}.jsonl"

        records: list[dict[str, Any]] = []
        for log_file in sorted(self.log_dir.glob("audit.*.jsonl")):
            if log_file == output or log_file.name.startswith("audit.export."):
                continue
            try:
                text = log_file.read_text()
            except OSError:
                continue
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entry_raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry_raw, dict):
                    continue
                entry = cast(dict[str, Any], entry_raw)
                if since is not None:
                    ts = entry.get("ts")
                    if isinstance(ts, str):
                        try:
                            entry_dt = datetime.fromisoformat(ts)
                        except ValueError:
                            continue
                        if entry_dt.tzinfo is None:
                            entry_dt = entry_dt.replace(tzinfo=timezone.utc)
                        if entry_dt < since:
                            continue
                records.append(entry)

        output.write_text("".join(json.dumps(record) + "\n" for record in records))
        return output

    def cleanup(self, retention_days: int | None = None) -> int:
        """Remove audit log files older than the retention period.

        Returns the number of files removed.
        """
        if retention_days is None:
            retention_days = self.config.audit.retention_days
        cutoff = datetime.now(timezone.utc).timestamp() - retention_days * 86400
        removed = 0
        for log_file in self.log_dir.glob("audit.*.jsonl"):
            if log_file == self.log_file or log_file.name.startswith("audit.export."):
                continue
            try:
                mtime = log_file.stat().st_mtime
            except OSError:
                continue
            if mtime < cutoff:
                try:
                    log_file.unlink()
                    removed += 1
                except OSError:
                    continue
        return removed

    def bind_context(self, **kwargs: Any) -> AuditLogger:
        """Bind extra context to future records.

        Bound values are merged into every subsequent audit record's payload.
        Explicit payload keys passed to ``record`` take precedence over bound
        context values. The logger instance is returned to allow chaining.
        """
        self._context.update(kwargs)
        return self

    def _redact(self, value: Any) -> Any:
        """Recursively remove sensitive keys from audit payloads."""
        if isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            redacted: dict[str, Any] = {}
            for key, item in value_dict.items():
                if any(s in key.lower() for s in SENSITIVE_KEYS):
                    redacted[key] = "***"
                else:
                    redacted[key] = self._redact(item)
            return redacted
        if isinstance(value, list):
            value_list = cast(list[Any], value)
            return [self._redact(item) for item in value_list]
        return value

    def _forward_to_siem(self, entry: dict[str, Any]) -> None:
        """Best-effort forward a single audit record to a configured SIEM.

        The record is redacted before transmission to avoid leaking tokens,
        credentials, or other secrets.
        """
        if self._siem_client is None:
            return
        try:
            self._siem_client.post("", json=self._redact(entry))
        except httpx.HTTPError as exc:
            logger.debug("Failed to forward audit record to SIEM: %s", exc)
