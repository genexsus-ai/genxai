# Audit Logging & Approvals

GenXAI records audit events and supports simple approval workflows for sensitive actions.

## Audit Log

```python
from genxai.security.audit import get_audit_log

events = get_audit_log().list_events()
```

Audit and approval data are persisted in SQLite by default at:

```
genxai/data/audit.db
```

You can override the path via `GENXAI_AUDIT_DB`.

## Approvals

```python
from genxai.security.audit import get_approval_service

approval = get_approval_service().submit("tool.execute", "tool:calculator", "alice")
get_approval_service().approve(approval.request_id)
```

Mark resources with `requires_approval=True` in access rules. Policy engine checks will
block access until the approval request is approved. Store the request id on the rule:

```python
from genxai.security.policy_engine import AccessRule

rule = AccessRule(
    permissions={Permission.TOOL_EXECUTE},
    allowed_users={"alice"},
    requires_approval=True,
    approval_request_id=approval.request_id,
)
```

If no approval request id is provided, the policy engine auto-submits an approval
request on first access attempt and blocks until it is approved.

## Default Policies

GenXAI ships with a helper to register example approval-aware policies:

```python
from genxai.security.default_policies import register_default_policies

register_default_policies()
```