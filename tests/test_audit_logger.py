"""Tests for AuditLogger."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

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
        self._siem_client = None

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


def test_audit_logger_export_filters_by_since(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-export"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    old_ts = "2020-01-01T00:00:00+00:00"
    new_ts = "2099-01-01T00:00:00+00:00"
    log_file = log_dir / "audit.2020-01-01.jsonl"
    log_file.write_text(json.dumps({"ts": old_ts, "event": "old"}) + "\n")
    audit.log_file.write_text(json.dumps({"ts": new_ts, "event": "new"}) + "\n")

    output = audit.export()
    lines = output.read_text().strip().splitlines()
    assert len(lines) == 2

    since = datetime(2090, 1, 1, tzinfo=timezone.utc)
    output_since = audit.export(since=since)
    lines_since = output_since.read_text().strip().splitlines()
    assert len(lines_since) == 1
    assert json.loads(lines_since[0])["event"] == "new"


def test_audit_logger_cleanup_removes_old_files(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-cleanup"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    old_file = log_dir / "audit.2020-01-01.jsonl"
    old_file.write_text('{"ts": "2020-01-01T00:00:00+00:00", "event": "old"}\n')
    new_file = log_dir / "audit.2099-01-01.jsonl"
    new_file.write_text('{"ts": "2099-01-01T00:00:00+00:00", "event": "new"}\n')

    # Set mtime far in the past for the old file so cleanup removes it.
    os.utime(old_file, (1, 1))

    removed = audit.cleanup(retention_days=30)
    assert removed == 1
    assert not old_file.exists()
    assert new_file.exists()
