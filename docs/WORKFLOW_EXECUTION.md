# Workflow Execution (Studio)

This guide explains how Studio executes workflows, the API endpoints involved,
and how payloads flow through the system.

---

## High-Level Flow

```text
Frontend (Studio) → FastAPI → workflow_executor → GenXAI core graph
```

1. User clicks **Run** in Studio.
2. Frontend calls `POST /api/workflows/{id}/execute`.
3. Backend loads workflow, validates, and runs it via core execution.
4. Result state is returned and shown in the UI.

---

## API Endpoints

### Execute Workflow

```
POST /api/workflows/{id}/execute
```

Example payload:

```json
{
  "input_data": {
    "topic": "AI adoption"
  }
}
```

Example response:

```json
{
  "status": "success",
  "result": {
    "output": "...",
    "state": {
      "topic": "AI adoption",
      "summary": "..."
    }
  }
}
```

---

## Execution Implementation

Primary implementation files:

- `studio/backend/api/workflows.py`
- `studio/backend/services/workflow_executor.py`
- `genxai/core/graph/engine.py`

The executor is responsible for:

- Loading workflow definitions (stored in Studio DB)
- Validating nodes and edges
- Injecting input data
- Running the graph
- Returning final state/output

---

## Validation & Errors

When a workflow is executed:

- Graph validation failures are surfaced as 4xx responses.
- Runtime execution failures return a structured error payload.

Typical error response:

```json
{
  "status": "error",
  "message": "Graph validation failed",
  "details": ["Missing node: agent_1"]
}
```

---

## Related Docs

- `docs/API_REFERENCE.md`
- `docs/WORKFLOW_BEST_PRACTICES.md`
- `studio/README.md`

