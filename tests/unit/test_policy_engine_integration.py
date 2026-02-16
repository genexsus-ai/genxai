"""Unit tests for policy engine integration points."""

import pytest

from genxai.core.memory.shared import SharedMemoryBus
from genxai_enterprise.security.policy_engine import AccessRule, get_policy_engine
from genxai_enterprise.security.rbac import Permission, Role, User, set_current_user, PermissionDenied


@pytest.mark.asyncio
async def test_shared_memory_policy_enforced():
    bus = SharedMemoryBus()
    policy = get_policy_engine()
    policy.add_rule(
        "memory:plan",
        AccessRule(permissions={Permission.MEMORY_READ, Permission.MEMORY_WRITE}, allowed_users={"alice"}),
    )

    set_current_user(User(user_id="bob", role=Role.DEVELOPER))
    with pytest.raises(PermissionDenied):
        await bus.set("plan", "value")

    set_current_user(User(user_id="alice", role=Role.DEVELOPER))
    await bus.set("plan", "value")
    assert bus.get("plan") == "value"