"""Resource-level policy engine for GenXAI."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set
from genxai.security.rbac import Permission, User, PermissionDenied

from genxai.security.audit import get_approval_service


class ResourceType(str, Enum):
    """Resource types covered by policy engine."""

    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    MEMORY = "memory"


@dataclass
class AccessRule:
    """ACL rule for a resource."""

    permissions: Set[Permission]
    allowed_users: Optional[Set[str]] = None
    requires_approval: bool = False
    approval_request_id: Optional[str] = None


class PolicyEngine:
    """Simple ACL-based policy engine."""

    def __init__(self) -> None:
        self._rules: Dict[str, AccessRule] = {}

    def add_rule(self, resource_id: str, rule: AccessRule) -> None:
        self._rules[resource_id] = rule

    def check(self, user: User, resource_id: str, permission: Permission) -> None:
        rule = self._rules.get(resource_id)
        if rule is None:
            if not user.has_permission(permission):
                raise PermissionDenied(
                    f"User {user.user_id} missing permission: {permission.value}"
                )
            return

        if rule.requires_approval:
            if not rule.approval_request_id:
                approval = get_approval_service().submit(
                    f"{permission.value}",
                    resource_id,
                    user.user_id,
                )
                rule.approval_request_id = approval.request_id
            approval = get_approval_service().get(rule.approval_request_id)
            if not approval or approval.status != "approved":
                raise PermissionDenied(
                    f"Approval required for resource {resource_id}"
                )

        if rule.allowed_users and user.user_id not in rule.allowed_users:
            raise PermissionDenied(
                f"User {user.user_id} not allowed for resource {resource_id}"
            )

        if permission not in rule.permissions:
            raise PermissionDenied(
                f"Permission {permission.value} denied for resource {resource_id}"
            )


_policy_engine: Optional[PolicyEngine] = None


def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


def _alias_enterprise_module() -> None:
    """Ensure enterprise.* imports resolve to this module instance."""
    module_name = __name__
    alias_name = "enterprise.genxai.security.policy_engine"
    sys.modules[alias_name] = sys.modules[module_name]
    sys.modules["genxai.security.policy_engine"] = sys.modules[module_name]


_alias_enterprise_module()