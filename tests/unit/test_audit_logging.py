"""Unit tests for audit logging and approvals."""

from enterprise.genxai.security.audit import get_audit_log, get_approval_service, AuditEvent


def test_audit_log_records_event():
    log = get_audit_log()
    log.record(AuditEvent(action="test", actor_id="u1", resource_id="r1", status="allowed"))
    assert log.list_events()[-1].action == "test"


def test_approval_service():
    approvals = get_approval_service()
    request = approvals.submit("tool.execute", "tool:x", "alice")
    approvals.approve(request.request_id)
    assert approvals.get(request.request_id).status == "approved"