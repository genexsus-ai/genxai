# Governance Policy Engine

GenXAI includes a resource‑level ACL policy engine layered on top of RBAC.

## How it works
- RBAC provides coarse permissions (`tool:execute`, `agent:read`, etc.)
- Policy engine enforces **resource‑specific** ACLs (e.g. tool `tool:csv_processor`)

## Example

```python
from genxai.security.policy_engine import get_policy_engine, AccessRule
from genxai.security.rbac import Permission, User, Role, set_current_user

policy = get_policy_engine()
policy.add_rule(
    "tool:calculator",
    AccessRule(permissions={Permission.TOOL_EXECUTE}, allowed_users={"alice"})
)

policy.add_rule(
    "agent:finance_agent",
    AccessRule(permissions={Permission.AGENT_EXECUTE}, allowed_users={"alice"})
)

policy.add_rule(
    "memory:shared_plan",
    AccessRule(permissions={Permission.MEMORY_READ, Permission.MEMORY_WRITE}, allowed_users={"alice"})
)

# Trigger-level policies
policy.add_rule(
    "trigger:webhook_inbound",
    AccessRule(permissions={Permission.TRIGGER_EXECUTE}, allowed_users={"alice", "bob"})
)

# Connector-level policies
policy.add_rule(
    "connector:kafka_events",
    AccessRule(permissions={Permission.CONNECTOR_READ, Permission.CONNECTOR_WRITE}, allowed_users={"alice"})
)

policy.add_rule(
    "connector:postgres_cdc",
    AccessRule(permissions={Permission.CONNECTOR_READ}, allowed_users={"alice", "bob"})
)

set_current_user(User(user_id="alice", role=Role.DEVELOPER))
# Tool, trigger, and connector execution will be allowed only for alice.
```

## Policy Enforcement Points

GenXAI enforces policies at multiple layers:

1. **Tool Execution**: Before executing any tool, the policy engine checks if the current user has `TOOL_EXECUTE` permission for that specific tool resource.
2. **Agent Execution**: Before running an agent, the policy engine validates `AGENT_EXECUTE` permission.
3. **Memory Access**: Read/write operations on shared memory require `MEMORY_READ`/`MEMORY_WRITE` permissions.
4. **Trigger Activation**: Triggers (webhook, schedule, queue, file watcher) require `TRIGGER_EXECUTE` permission.
5. **Connector Operations**: Connectors (webhook, Kafka, SQS, Postgres CDC) require `CONNECTOR_READ`/`CONNECTOR_WRITE` permissions.

## Best Practices

- **Principle of Least Privilege**: Grant only the minimum permissions required for each user/role.
- **Resource-Specific Rules**: Use fine-grained ACLs for sensitive tools, triggers, and connectors.
- **Audit Logging**: Enable audit logging to track all policy decisions and access attempts.
- **Regular Reviews**: Periodically review and update policies as your system evolves.
