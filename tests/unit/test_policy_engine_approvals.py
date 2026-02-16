"""Tests for approval enforcement in policy engine."""

import pytest

from genxai_enterprise.security.policy_engine import AccessRule, get_policy_engine
from genxai_enterprise.security.rbac import Permission, Role, User, PermissionDenied
from genxai_enterprise.security.audit import get_approval_service


def test_policy_engine_requires_approval():
    engine = get_policy_engine()
    engine.add_rule(
        "tool:secure",
        AccessRule(
            permissions={Permission.TOOL_EXECUTE},
            allowed_users={"alice"},
            requires_approval=True,
        ),
    )
    user = User(user_id="alice", role=Role.DEVELOPER)

    with pytest.raises(PermissionDenied):
        engine.check(user, "tool:secure", Permission.TOOL_EXECUTE)

    approval = get_approval_service().get("approval_1")
    assert approval is not None
    get_approval_service().approve(approval.request_id)

    engine.check(user, "tool:secure", Permission.TOOL_EXECUTE)