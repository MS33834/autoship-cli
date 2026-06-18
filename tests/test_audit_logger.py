"""Tests for AuditLogger."""

from __future__ import annotations

import json

from autoship.core.audit_logger import AuditLogger
from autoship.models.config import AppConfig


def test_audit_logger_creates_log_file(project_root, app_config: AppConfig, monkeypatch) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-123"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)
    audit.record("test.event", {"key": "value"})

    assert audit.log_file.exists()
    lines = audit.log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "test.event"
    assert entry["trace_id"] == "trace-123"
    assert entry["payload"]["key"] == "value"


def test_audit_logger_bind_context_returns_self(app_config: AppConfig) -> None:
    audit = AuditLogger(app_config)
    bound = audit.bind_context(extra="value")
    assert bound is audit
