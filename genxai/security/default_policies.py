"""Default policy setup with explicit approval request IDs."""

from genxai.security.audit import get_approval_service
from genxai.security.policy_engine import AccessRule, get_policy_engine
from genxai.security.rbac import Permission


def register_default_policies() -> None:
    """Register default policies with explicit approval IDs."""
    policy = get_policy_engine()
    approvals = get_approval_service()

    tool_approval = approvals.submit("tool.execute", "tool:calculator", "system")
    policy.add_rule(
        "tool:calculator",
        AccessRule(
            permissions={Permission.TOOL_EXECUTE},
            allowed_users={"admin"},
            requires_approval=True,
            approval_request_id=tool_approval.request_id,
        ),
    )

    agent_approval = approvals.submit("agent.execute", "agent:finance_agent", "system")
    policy.add_rule(
        "agent:finance_agent",
        AccessRule(
            permissions={Permission.AGENT_EXECUTE},
            allowed_users={"admin"},
            requires_approval=True,
            approval_request_id=agent_approval.request_id,
        ),
    )

    workflow_approval = approvals.submit("workflow.execute", "workflow:workflow", "system")
    policy.add_rule(
        "workflow:workflow",
        AccessRule(
            permissions={Permission.WORKFLOW_EXECUTE},
            allowed_users={"admin"},
            requires_approval=True,
            approval_request_id=workflow_approval.request_id,
        ),
    )