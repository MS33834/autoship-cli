"""Tests for AuditLogger."""

from __future__ import annotations

import json
import os
import stat
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


def test_audit_logger_bind_context_merges_into_records(
    project_root, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-bind"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None
        self._context = {}

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)
    audit.bind_context(user="alice", env="prod")
    audit.record("test.bound", {"action": "deploy"})
    audit.record("test.override", {"action": "verify", "user": "bob"})

    lines = audit.log_file.read_text().strip().splitlines()
    assert len(lines) == 2
    bound_entry = json.loads(lines[0])
    assert bound_entry["payload"]["user"] == "alice"
    assert bound_entry["payload"]["env"] == "prod"
    assert bound_entry["payload"]["action"] == "deploy"
    override_entry = json.loads(lines[1])
    assert override_entry["payload"]["user"] == "bob"
    assert override_entry["payload"]["env"] == "prod"


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


def test_audit_logger_redacts_secret_values_by_pattern(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-pattern"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None
        self._context = {}

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    github_token = "ghp_" + "a" * 36
    openai_key = "sk-" + "b" * 48
    audit.record(
        "test.patterns",
        {
            "message": f"Authorization: Bearer {github_token}",
            "openai_api_key": openai_key,
            "aws_key": "AKIAIOSFODNN7EXAMPLE",
            "nested": {
                "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            },
            "safe": "plain text without secrets",
        },
    )

    lines = audit.log_file.read_text().strip().splitlines()
    entry = json.loads(lines[0])
    payload = entry["payload"]
    assert payload["message"] == "***"
    assert payload["openai_api_key"] == "***"
    assert payload["aws_key"] == "***"
    assert payload["nested"]["jwt"] == "***"
    assert payload["safe"] == "plain text without secrets"


def test_audit_logger_exact_key_match_not_substring(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.trace_id = "trace-exact"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None
        self._context = {}

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    audit.record(
        "test.exact",
        {
            "mytoken": "not-redacted-by-key",
            "api_key": "redacted-by-key",
            "token_value": "ghp_" + "c" * 36,
        },
    )

    lines = audit.log_file.read_text().strip().splitlines()
    payload = json.loads(lines[0])["payload"]
    assert payload["mytoken"] == "not-redacted-by-key"
    assert payload["api_key"] == "***"
    assert payload["token_value"] == "***"


def test_audit_logger_sets_restrictive_permissions(tmp_path: Path) -> None:
    """Audit log directory and file are only owner-readable/writable."""
    log_dir = tmp_path / "logs"
    config = AppConfig(audit_log_dir=log_dir)
    audit = AuditLogger(config)

    audit.record("test.permissions", {"status": "ok"})

    assert audit.log_dir.exists()
    assert stat.S_IMODE(audit.log_dir.stat().st_mode) == 0o700
    assert audit.log_file.exists()
    assert stat.S_IMODE(audit.log_file.stat().st_mode) == 0o600


def test_audit_logger_export_sets_restrictive_permissions(
    tmp_path: Path, monkeypatch
) -> None:
    """Exported audit files are only owner-readable/writable."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audit.2099-01-01.jsonl"
    log_file.write_text(json.dumps({"ts": "2099-01-01T00:00:00+00:00", "event": "x"}) + "\n")

    config = AppConfig(audit_log_dir=log_dir)
    audit = AuditLogger(config)
    output = audit.export()

    assert output.exists()
    assert stat.S_IMODE(output.stat().st_mode) == 0o600


def test_audit_logger_redact_unknown_fields(
    project_root: Path, app_config: AppConfig, monkeypatch
) -> None:
    log_dir = project_root / "logs"

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.config.audit.redact_unknown_fields = True
        self.trace_id = "trace-unknown"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = None
        self._context = {}

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    audit.record(
        "test.unknown",
        {
            "command": "deploy",
            "returncode": 0,
            "unknown_field": "secret",
            "details": {"value": "kept", "another_unknown": "data"},
        },
    )

    lines = audit.log_file.read_text().strip().splitlines()
    payload = json.loads(lines[0])["payload"]
    assert payload["command"] == "deploy"
    assert payload["returncode"] == 0
    assert payload["unknown_field"] == "***"
    assert payload["details"]["value"] == "kept"
    assert payload["details"]["another_unknown"] == "***"


def test_audit_logger_disables_siem_after_consecutive_failures(
    project_root: Path, app_config: AppConfig, monkeypatch, caplog
) -> None:
    log_dir = project_root / "logs"

    class FailingClient:
        def __init__(self) -> None:
            self.calls = 0

        def post(self, _path: str, *, json: object) -> None:
            self.calls += 1
            raise httpx.ConnectError("connection refused")

    def _init(self: AuditLogger, config: AppConfig) -> None:
        self.config = config
        self.config.audit.siem_enabled = True
        self.config.audit.siem_url = "https://siem.example.com"
        self.config.audit.siem_max_failures = 2
        self.trace_id = "trace-siem-failures"
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit.test.jsonl"
        self._siem_client = FailingClient()
        self._context = {}
        self._siem_failures = 0
        self._siem_disabled = False

    monkeypatch.setattr(AuditLogger, "__init__", _init)
    audit = AuditLogger(app_config)

    with caplog.at_level("WARNING", logger="autoship"):
        audit.record("test.siem_1", {"status": "value"})
        audit.record("test.siem_2", {"status": "value"})
        # After 2 failures, forwarding should be disabled.
        audit.record("test.siem_3", {"status": "value"})

    assert audit._siem_disabled is True
    assert audit._siem_failures == 2
    assert "SIEM forwarding has failed 2 consecutive times" in caplog.text
    # The failing client should have been called exactly twice, not three times.
    assert audit._siem_client is not None
    assert audit._siem_client.calls == 2
