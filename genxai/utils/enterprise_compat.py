"""Enterprise-compatibility shims for the OSS package.

The OSS `genxai` package must be usable without any `enterprise.*` modules.
However, during development in the monorepo (or when the enterprise package is
installed), OSS code can take advantage of enterprise features (audit logging,
RBAC/policy checks, metrics/tracing).

This module provides a stable import surface that:

- uses real enterprise implementations when available
- otherwise falls back to safe no-ops / permissive defaults

This enables the "Option A" CLI split:

- OSS ships `genxai` executable + core commands
- enterprise adds commands via entry-point plugins
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, Optional


# ---------------------------------------------------------------------------
# Security / RBAC / policy
# ---------------------------------------------------------------------------


class Permission(str, Enum):
    """Minimal permission enum used by OSS code paths.

    The enterprise implementation may define additional permissions.
    """

    AGENT_EXECUTE = "agent.execute"
    WORKFLOW_EXECUTE = "workflow.execute"
    TOOL_EXECUTE = "tool.execute"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"


class _NullPolicyEngine:
    def check(self, user: Any, resource: str, permission: Permission) -> None:  # noqa: ARG002
        return


class _NullUser:
    user_id: str = "anonymous"


def get_current_user() -> Optional[Any]:
    return None


def get_policy_engine() -> Any:
    return _NullPolicyEngine()


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@dataclass
class AuditEvent:
    action: str
    actor_id: str
    resource_id: str
    status: str


class _NullAuditLog:
    def record(self, event: AuditEvent) -> None:  # noqa: ARG002
        return


def get_audit_log() -> Any:
    return _NullAuditLog()


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------


def set_log_context(**kwargs: Any) -> None:  # noqa: ARG001
    return


def clear_log_context() -> None:
    return


@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[None]:  # noqa: ARG001
    yield


def add_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:  # noqa: ARG001
    return


def record_exception(exc: BaseException) -> None:  # noqa: ARG001
    return


def record_tool_execution(
    tool_name: str,
    duration: float,
    status: str = "success",
    error_type: Optional[str] = None,
) -> None:  # noqa: ARG001
    return


def record_agent_execution(
    agent_id: str,
    duration: float,
    status: str = "success",
    error_type: Optional[str] = None,
) -> None:  # noqa: ARG001
    return


def record_llm_request(
    provider: str,
    model: str,
    duration: float,
    status: str = "success",
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_cost: float = 0.0,
) -> None:  # noqa: ARG001
    return


def record_workflow_execution(
    workflow_id: str,
    duration: float,
    status: str = "success",
) -> None:  # noqa: ARG001
    return


def record_workflow_node_execution(
    workflow_id: str,
    node_id: str,
    status: str = "success",
) -> None:  # noqa: ARG001
    return


# ---------------------------------------------------------------------------
# Attempt to replace no-ops with enterprise implementations when present.
# ---------------------------------------------------------------------------


try:  # pragma: no cover
    from enterprise.genxai.observability.logging import (  # type: ignore
        set_log_context as _set_log_context,
        clear_log_context as _clear_log_context,
    )
    from enterprise.genxai.observability.metrics import (  # type: ignore
        record_tool_execution as _record_tool_execution,
        record_agent_execution as _record_agent_execution,
        record_llm_request as _record_llm_request,
        record_workflow_execution as _record_workflow_execution,
        record_workflow_node_execution as _record_workflow_node_execution,
    )
    from enterprise.genxai.observability.tracing import (  # type: ignore
        span as _span,
        add_event as _add_event,
        record_exception as _record_exception,
    )
    from enterprise.genxai.security.rbac import (  # type: ignore
        get_current_user as _get_current_user,
        Permission as _Permission,
    )
    from enterprise.genxai.security.policy_engine import (  # type: ignore
        get_policy_engine as _get_policy_engine,
    )
    from enterprise.genxai.security.audit import (  # type: ignore
        get_audit_log as _get_audit_log,
        AuditEvent as _AuditEvent,
    )

    # Replace with enterprise implementations.
    Permission = _Permission  # type: ignore[assignment]
    get_current_user = _get_current_user  # type: ignore[assignment]
    get_policy_engine = _get_policy_engine  # type: ignore[assignment]
    get_audit_log = _get_audit_log  # type: ignore[assignment]
    AuditEvent = _AuditEvent  # type: ignore[assignment]

    set_log_context = _set_log_context  # type: ignore[assignment]
    clear_log_context = _clear_log_context  # type: ignore[assignment]
    span = _span  # type: ignore[assignment]
    add_event = _add_event  # type: ignore[assignment]
    record_exception = _record_exception  # type: ignore[assignment]

    record_tool_execution = _record_tool_execution  # type: ignore[assignment]
    record_agent_execution = _record_agent_execution  # type: ignore[assignment]
    record_llm_request = _record_llm_request  # type: ignore[assignment]
    record_workflow_execution = _record_workflow_execution  # type: ignore[assignment]
    record_workflow_node_execution = _record_workflow_node_execution  # type: ignore[assignment]
except Exception:
    # Enterprise not installed / import failed -> keep OSS-safe no-ops.
    pass
