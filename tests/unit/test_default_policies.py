"""Tests for default policy registration with explicit approvals."""
from genxai_enterprise.security.default_policies import register_default_policies
from genxai_enterprise.security.audit import get_approval_service

from genxai_enterprise.security.policy_engine import get_policy_engine


def test_register_default_policies_creates_approvals():
    register_default_policies()
    approvals = get_approval_service()
    assert approvals.get("approval_1") is not None
    assert approvals.get("approval_2") is not None
    assert approvals.get("approval_3") is not None

    policy = get_policy_engine()
    assert "tool:calculator" in policy._rules
    assert "agent:finance_agent" in policy._rules
    assert "workflow:workflow" in policy._rules