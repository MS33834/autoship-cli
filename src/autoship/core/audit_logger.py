"""Structured audit logging for security and observability."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")


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
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": self.trace_id,
            "event": event,
            "payload": self._redact(payload or {}),
        }
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError as exc:
            logger.warning("Failed to write audit record for %s: %s", event, exc)
        self._forward_to_siem(entry)

    def _redact(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive keys from audit payloads."""
        sensitive = {"api_key", "token", "password", "secret", "credentials"}
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if any(s in key.lower() for s in sensitive):
                redacted[key] = "***"
            else:
                redacted[key] = value
        return redacted

    def _forward_to_siem(self, entry: dict[str, Any]) -> None:
        """Best-effort forward a single audit record to a configured SIEM."""
        if self._siem_client is None:
            return
        try:
            self._siem_client.post("", json=entry)
        except httpx.HTTPError as exc:
            logger.debug("Failed to forward audit record to SIEM: %s", exc)

    def export(
        self,
        since: datetime | None = None,
        output: Path | None = None,
    ) -> Path:
        """Export audit records newer than ``since`` to a JSON Lines file.

        If ``output`` is not provided, a timestamped file is created in the
        current audit log directory.
        """
        if output is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            output = self.log_dir / f"audit-export.{timestamp}.jsonl"
        output = Path(output)

        if since is None:
            cutoff = datetime.min.replace(tzinfo=timezone.utc)
        else:
            cutoff = since.astimezone(timezone.utc)

        exported = 0
        with output.open("w", encoding="utf-8") as out:
            for log_file in sorted(self.log_dir.glob("audit.*.jsonl")):
                try:
                    with log_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            ts = self._parse_ts(record.get("ts", ""))
                            if ts is None or ts >= cutoff:
                                out.write(line + "\n")
                                exported += 1
                except OSError as exc:
                    logger.warning("Failed to read audit file %s: %s", log_file, exc)

        logger.info("Exported %d audit records to %s", exported, output)
        return output

    def _parse_ts(self, value: Any) -> datetime | None:
        """Parse an ISO timestamp string, returning None on failure."""
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None

    def cleanup(self, retention_days: int | None = None) -> int:
        """Remove audit log files older than the retention period."""
        days = retention_days if retention_days is not None else self.config.audit.retention_days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        removed = 0
        for log_file in self.log_dir.glob("audit.*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    log_file.unlink()
                    removed += 1
            except OSError as exc:
                logger.warning("Failed to remove old audit file %s: %s", log_file, exc)
        return removed

    def bind_context(self, **kwargs: Any) -> AuditLogger:
        """Return a new logger with additional default payload fields."""
        # Placeholder for future enrichment; currently returns self.
        return self
