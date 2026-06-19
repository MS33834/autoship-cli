"""Tests for AuditLogger."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

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
    audit.record("test.event", {"status": "value"})

    assert audit.log_file.exists()
    lines = audit.log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["event"] == "test.event"
    assert entry["trace_id"] == "trace-123"
    assert entry["payload"]["status"] == "value"


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


def test_audit_logger_redacts_sensitive_fields(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-redact"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    audit.record(
        "test.secrets",
        {
            "event_type": "command",
            "command": "deploy",
            "returncode": 0,
            "duration_ms": 42,
            "api_key": "super-secret",
            "nested": {"password": "nested-secret", "siem_token": "token123"},
            "items": [{"private": "private123"}, {"ok": "value"}],
        },
    )

    lines = audit.log_file.read_text().strip().splitlines()
    entry = json.loads(lines[0])
    payload = entry["payload"]
    assert payload["event_type"] == "command"
    assert payload["command"] == "deploy"
    assert payload["returncode"] == 0
    assert payload["duration_ms"] == 42
    assert payload["api_key"] == "***"
    assert payload["nested"]["password"] == "***"
    assert payload["nested"]["siem_token"] == "***"
    assert payload["items"][0]["private"] == "***"
    assert payload["items"][1]["ok"] == "value"


def test_audit_logger_forwards_redacted_record_to_siem(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"
    posted: list[dict[str, object]] = []

    class FakeClient:
        def post(self, _path: str, *, json: dict[str, object]) -> None:
            posted.append(json)

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-siem"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = FakeClient()

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    audit.record(
        "test.siem",
        {"command": "deploy", "api_key": "secret", "nested": {"token": "tok"}},
    )

    assert len(posted) == 1
    forwarded = posted[0]
    assert forwarded["event"] == "test.siem"
    assert forwarded["payload"]["command"] == "deploy"
    assert forwarded["payload"]["api_key"] == "***"
    assert forwarded["payload"]["nested"]["token"] == "***"


def test_audit_logger_siem_failure_is_best_effort(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    class FailingClient:
        def post(self, _path: str, *, json: object) -> None:
            raise httpx.ConnectError("connection refused")

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-siem-fail"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = FailingClient()

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    # Should not raise despite SIEM being down.
    audit.record("test.siem_fail", {"status": "value"})

    assert audit.log_file.exists()
