"""Structured audit logging for security and observability."""

from __future__ import annotations

import json
import logging
import re
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import httpx

from autoship.models.config import AppConfig

logger = logging.getLogger("autoship")


def _ensure_dir_permissions(path: Path, mode: int) -> None:
    """Create ``path`` and enforce ``mode``, warning if it was too broad."""
    path.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _warn_if_too_broad(path, mode)
        path.chmod(mode)


def _ensure_file_permissions(path: Path, mode: int) -> None:
    """Enforce ``mode`` on ``path``, warning if it was too broad."""
    if path.exists():
        _warn_if_too_broad(path, mode)
    path.chmod(mode)


def _warn_if_too_broad(path: Path, mode: int) -> None:
    """Log a warning when ``path`` has permission bits beyond ``mode``."""
    current = stat.S_IMODE(path.stat().st_mode)
    if current & ~mode:
        logger.warning(
            "Permissions on %s (%04o) are too broad; tightening to %04o",
            path,
            current,
            mode,
        )


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
        "private_key",
        "credentials",
        "auth",
        "authorization",
        "access_token",
        "refresh_token",
    }
)

# Patterns that indicate a scalar string contains a secret or high-entropy token.
_SENSITIVE_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        # GitHub personal access token (classic)
        r"ghp_[A-Za-z0-9_]{36}",
        # GitHub fine-grained personal access token
        r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}",
        # OpenAI API key
        r"sk-[a-zA-Z0-9]{48}",
        # AWS access key id
        r"AKIA[0-9A-Z]{16}",
        # PEM/SSH private key block
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY-----",
        # JWT (header.payload.signature)
        r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
    )
)


def redact_text(text: str) -> str:
    """Redact a free-form string when it contains a secret-like pattern.

    This mirrors ``AuditLogger._redact_scalar`` so that unstructured text such
    as command stdout/stderr can be sanitized without an ``AuditLogger``
    instance.
    """
    if any(pattern.search(text) for pattern in _SENSITIVE_VALUE_PATTERNS):
        return "***"
    return text


# Keys that are safe to retain when ``redact_unknown_fields`` is enabled.
_SAFE_KEYS = frozenset(
    {
        "ts",
        "trace_id",
        "event",
        "payload",
        "event_type",
        "command",
        "commands",
        "returncode",
        "duration_ms",
        "status",
        "action",
        "actions",
        "user",
        "env",
        "environment",
        "plugin_name",
        "plugin",
        "version",
        "path",
        "paths",
        "target",
        "targets",
        "message",
        "messages",
        "error",
        "errors",
        "description",
        "output",
        "result",
        "details",
        "config",
        "args",
        "cwd",
        "project_type",
        "detected",
        "fix",
        "count",
        "removed",
        "since",
        "reason",
        "operation",
        "enabled",
        "value",
        "values",
        "name",
        "names",
        "id",
        "ids",
        "type",
        "types",
        "source",
        "sources",
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
        self._siem_failures: int = 0
        self._siem_disabled: bool = False
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
            _ensure_dir_permissions(self.log_dir, 0o700)
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
            _ensure_file_permissions(self.log_file, 0o600)
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
        _ensure_file_permissions(output, 0o600)
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

    def _redact(self, value: Any, *, _unknown: bool | None = None) -> Any:
        """Recursively redact sensitive keys and secret-like values.

        When ``config.audit.redact_unknown_fields`` is enabled, any key that is
        not explicitly known to be safe is redacted to avoid leaking data that
        accidentally ends up in an audit record.
        """
        if _unknown is None:
            _unknown = self.config.audit.redact_unknown_fields
        if isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            redacted: dict[str, Any] = {}
            for key, item in value_dict.items():
                key_lower = key.lower()
                if self._is_sensitive_key(key_lower):
                    redacted[key] = "***"
                elif key_lower in _SAFE_KEYS or not _unknown:
                    redacted[key] = self._redact(item, _unknown=_unknown)
                else:
                    redacted[key] = self._redact_unknown_value(item)
            return redacted
        if isinstance(value, list):
            value_list = cast(list[Any], value)
            return [self._redact(item, _unknown=_unknown) for item in value_list]
        return self._redact_scalar(value)

    def _is_sensitive_key(self, key: str) -> bool:
        """Return True if ``key`` is a known sensitive field name."""
        return key in SENSITIVE_KEYS

    def _redact_scalar(self, value: Any) -> Any:
        """Redact a scalar value if it contains a secret-like pattern."""
        if isinstance(value, str):
            return redact_text(value)
        return value

    def _redact_unknown_value(self, value: Any) -> Any:
        """Redact an unknown value recursively.

        Dictionaries and lists are traversed so that any nested unknown fields
        are also redacted; scalars are replaced with a mask.
        """
        if isinstance(value, dict):
            return self._redact(value, _unknown=True)
        if isinstance(value, list):
            value_list = cast(list[Any], value)
            return [self._redact_unknown_value(item) for item in value_list]
        return "***"

    def _forward_to_siem(self, entry: dict[str, Any]) -> None:
        """Best-effort forward a single audit record to a configured SIEM.

        The record is redacted before transmission to avoid leaking tokens,
        credentials, or other secrets.

        After ``config.audit.siem_max_failures`` consecutive failures, SIEM
        forwarding is disabled and a warning is emitted to avoid spamming a
        down endpoint.
        """
        if self._siem_client is None or getattr(self, "_siem_disabled", False):
            return
        try:
            self._siem_client.post("", json=self._redact(entry))
        except httpx.HTTPError as exc:
            self._siem_failures = getattr(self, "_siem_failures", 0) + 1
            logger.debug("Failed to forward audit record to SIEM: %s", exc)
            if self._siem_failures >= self.config.audit.siem_max_failures:
                self._siem_disabled = True
                logger.warning(
                    "SIEM forwarding has failed %d consecutive times and is now disabled.",
                    self._siem_failures,
                )
        else:
            self._siem_failures = 0
