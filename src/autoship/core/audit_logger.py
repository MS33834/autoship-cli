"""Structured audit logging for security and observability."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")


class AuditLogger:
    """Append-only JSONL audit logger.

    Logs are written to ``~/.autoship/logs/audit.{YYYY-MM-DD}.jsonl``
    by default, or to ``config.audit_log_dir`` when provided.
    Each command invocation shares a single ``trace_id``.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.trace_id = str(uuid.uuid4())
        log_dir = (
            config.audit_log_dir if config.audit_log_dir else Path.home() / ".autoship" / "logs"
        )
        self.log_dir = Path(log_dir)
        self._ensure_log_dir()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"audit.{today}.jsonl"

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

    def bind_context(self, **kwargs: Any) -> AuditLogger:
        """Return a new logger with additional default payload fields."""
        # Placeholder for future enrichment; currently returns self.
        return self
