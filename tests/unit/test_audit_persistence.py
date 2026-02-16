"""Tests for SQLite-backed audit persistence."""

import os

from enterprise.genxai.security.audit import AuditEvent, get_audit_log, get_approval_service, reset_audit_services


def test_audit_persistence(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("GENXAI_AUDIT_DB", str(db_path))
    reset_audit_services()

    log = get_audit_log()
    log.record(
        AuditEvent(
            action="tool.execute",
            actor_id="alice",
            resource_id="tool:x",
            status="success",
        )
    )

    reset_audit_services()
    log = get_audit_log()
    events = log.list_events()
    assert len(events) == 1
    assert events[0].action == "tool.execute"

    approval = get_approval_service().submit("tool.execute", "tool:x", "alice")
    reset_audit_services()
    approval_service = get_approval_service()
    assert approval_service.get(approval.request_id) is not None

    reset_audit_services()
    os.environ.pop("GENXAI_AUDIT_DB", None)