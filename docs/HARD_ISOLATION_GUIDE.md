# Hard Isolation Guide (Process/Runtime Isolation)

This guide explains how to achieve **hard isolation** for agents in GenXAI.

## What “Hard Isolation” Means

- **Logical isolation** (default): agents have separate runtime objects and memory contexts.
- **Hard isolation**: agents run in **separate OS processes/containers** with explicit communication boundaries.

In GenXAI today, logical isolation is built-in. Hard isolation is achieved by deployment architecture.

---

## Isolation Levels in GenXAI

### 1) Default (Logical Isolation)

- Each agent is executed through its own `AgentRuntime`.
- Runtime state (`_memory`, `_tools`, context) is isolated per runtime instance.
- Shared state only appears when explicitly enabled (for example, shared memory bus).

### 2) Hard Isolation (Recommended for Sensitive/Multitenant Workloads)

Use separate workers/processes and route tasks through a queue backend.

---

## When You Should Use Hard Isolation

Use hard isolation when you need:

- Multi-tenant separation with stronger blast-radius control
- Compliance/security boundaries
- Untrusted or high-risk tool execution
- Independent scaling and failure domains per agent class

---

## What Exists in the Current Codebase

You can build hard isolation with current OSS components:

- `WorkerQueueEngine`
- `RedisQueueBackend` (cross-process friendly)
- Handler registry and queue-based dispatch patterns

This means you do **not** need a framework fork—just an isolation-focused deployment pattern.

---

## Reference Architecture

1. **Orchestrator service**
   - Accepts workflow requests
   - Enqueues work into Redis queue

2. **Dedicated worker pools** (separate process/container)
   - Pool A: `research` agents
   - Pool B: `review` agents
   - Pool C: `sensitive` agents

3. **Strict boundaries**
   - Separate secrets per worker pool
   - Separate filesystem mounts
   - Restricted network egress per pool

4. **Memory/data partitioning**
   - Namespace by tenant + workflow + agent id
   - Disable shared memory unless explicitly required

---

## Step-by-Step Implementation

## 1) Disable Shared Memory by Default

If you need strict separation, keep workflow shared memory off:

```yaml
workflow:
  memory:
    shared: false
    enabled: false
```

Only enable shared memory for explicitly trusted collaboration cases.

## 2) Use Redis Queue Backend

```python
from genxai.core.execution import WorkerQueueEngine, RedisQueueBackend

backend = RedisQueueBackend(url="redis://localhost:6379/0")
engine = WorkerQueueEngine(backend=backend, worker_count=4)
```

## 3) Register Role-Specific Handlers

```python
async def research_handler(payload: dict):
    # run only research-class agents here
    ...

async def review_handler(payload: dict):
    # run only review-class agents here
    ...

engine.register_handler("research", research_handler)
engine.register_handler("review", review_handler)
```

## 4) Route Tasks by Agent Class/Role

```python
await engine.enqueue(
    payload={"run_id": run_id, "task": task, "agent_role": "research"},
    handler_name="research",
    run_id=run_id,
)
```

## 5) Run Workers as Separate Processes/Containers

- Deploy each handler group in separate deployment/unit
- Give each deployment only required environment variables and credentials
- Apply CPU/memory limits and restart policies per deployment

## 6) Partition Memory and Persistence

Use partition keys in persistent backends:

- `tenant_id`
- `workflow_id`
- `agent_id`
- `run_id` (optional for short-lived contexts)

Never share a persistence namespace across tenants unless intentionally designed.

---

## Security Checklist for Hard Isolation

- [ ] Shared memory disabled by default
- [ ] Separate process/container per trust boundary
- [ ] Per-worker credentials (no global super-token)
- [ ] Restricted network egress (allowlist only)
- [ ] Read-only root FS where possible
- [ ] Separate memory/data namespaces per tenant/agent
- [ ] Queue retry/backoff and poison-message handling configured
- [ ] Audit logging enabled for workflow and agent execution

---

## Operational Best Practices

- **Idempotency**: provide stable `run_id` on enqueue
- **Retry policy**: bounded retries + backoff
- **Dead-letter strategy**: send repeatedly failing tasks to a review queue
- **Observability**: emit metrics for queue depth, retry count, failure rate, and per-worker latency
- **Autoscaling**: scale workers by queue depth per role

---

## Migration Path (Low Risk)

1. Start with current logical isolation setup
2. Move queue backend from in-memory to Redis
3. Split one sensitive role into a dedicated worker deployment
4. Add per-role credentials and egress policies
5. Expand separation role-by-role

This incremental approach avoids a disruptive rewrite.

---

## Common Pitfalls

- Assuming “same process” equals hard isolation (it does not)
- Accidentally enabling workflow shared memory globally
- Sharing one persistence namespace across tenants
- Reusing one API key/secrets bundle for all workers

---

## Summary

GenXAI already provides strong **logical isolation** by default. For **hard isolation**, use the existing queue engine and deploy role-specific workers in separate processes/containers with strict secret, network, and storage boundaries.
