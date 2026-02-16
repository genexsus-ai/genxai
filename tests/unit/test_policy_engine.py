"""Unit tests for policy engine."""

import pytest

from genxai_enterprise.security.policy_engine import AccessRule, get_policy_engine
from genxai_enterprise.security.rbac import Permission, User, Role, PermissionDenied


def test_policy_engine_allows_rbac():
    engine = get_policy_engine()
    user = User(user_id="dev", role=Role.DEVELOPER)
    engine.check(user, "tool:any", Permission.TOOL_EXECUTE)


def test_policy_engine_denies_acl():
    engine = get_policy_engine()
    engine.add_rule(
        "tool:sensitive",
        AccessRule(permissions={Permission.TOOL_EXECUTE}, allowed_users={"alice"}),
    )
    user = User(user_id="bob", role=Role.DEVELOPER)

    with pytest.raises(PermissionDenied):
        engine.check(user, "tool:sensitive", Permission.TOOL_EXECUTE)