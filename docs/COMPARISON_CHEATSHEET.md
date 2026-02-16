# CrewAI vs GenXAI — Condensed Cheatsheet

Quick, high-signal summary for mapping CrewAI concepts to GenXAI.

---

## 1) Core Concept Mapping

| CrewAI | GenXAI | Notes |
|---|---|---|
| Agent | Agent | Same concept. `AgentFactory.create_agent(...)` |
| Task | Workflow step (Graph node) | Each task becomes a node in a graph/flow. |
| Task.description | Runtime task input | `AgentRuntime.execute(task=...)` or `graph.run(input_data=...)` |
| Task.expected_output | Agent goal + validation | Put format in `goal`, enforce via validation/critic/conditions. |
| Task order | Edges / Conditions / Loops | Express dependencies in the graph. |

---

## 2) Quick Examples

### CrewAI Task
```python
Task(
  description="Research AI adoption",
  agent=researcher,
  expected_output="List 5 reputable sources"
)
```

### GenXAI Equivalent (Node + Goal + Validation)
```python
researcher = AgentFactory.create_agent(
  id="researcher",
  role="Researcher",
  goal="Return 5 reputable sources with summaries"
)

graph.add_node(AgentNode(id="research_task", agent_id=researcher.id))
# Validate output with ConditionNode or critic flow
```

---

## 3) Common Task Patterns → GenXAI Flows

| CrewAI Pattern | GenXAI Flow |
|---|---|
| Sequential tasks | `RoundRobinFlow` or Graph edges |
| Conditional tasks | `ConditionalFlow` / `RouterFlow` |
| Parallel tasks | `ParallelFlow` |
| Iterative refinement | `LoopFlow` / critic loop |
| Multi-task same agent | Reuse same `agent_id` in multiple nodes |
| Task bidding | `AuctionFlow` |
| Subtasks | `SubworkflowFlow` / `SubgraphNode` |
| Map/Reduce | `MapReduceFlow` |
| Coordinator/Worker | `CoordinatorWorkerFlow` |

---

## 3.1) CrewAI Pattern Mapping (Quick)

| CrewAI Pattern | GenXAI Equivalent |
|---|---|
| Sequential | `RoundRobinFlow` or graph edges |
| Parallel | `ParallelFlow` |
| Hierarchical | `CoordinatorWorkerFlow` / `SubworkflowFlow` |
| Hybrid | Combine multiple node types in one graph |
| Async | Native `async/await` execution |

---

## 4) Expected Output Enforcement Options

- **Prompt/Goal** (soft): `Agent.goal = "Write 2 paragraphs with citations"`
- **Validation Node** (hard): `ConditionNode` + loop
- **Critic Loop** (hard): `CriticReviewFlow`
- **Schema Validation** (hard): enforce state structure

---

## 5) Beyond Tasks

- **Memory**: Built-in short/long/episodic/semantic memory
- **Tools**: Central tool registry + schema-based tool calling
- **Triggers/Connectors**: Event-driven workflows (webhooks, schedules, Kafka, etc.)
- **Observability**: Built-in metrics + tracing hooks

---

## 6) Which One Is Better?

**Honest answer:** it depends on your needs.

- **CrewAI**: best for simpler task-first APIs and mostly sequential workflows.
- **GenXAI**: best for graph orchestration, memory, tools/registry, triggers, and
  enterprise-grade runtime capabilities.

---

## 7) Usage & Cost Tracking

- **Usage**: token usage tracked per agent; metrics API via `genxai metrics serve`.
- **Cost**: detailed cost tracking per agent/task is currently a roadmap item.

---

## References

- `docs/COMPARISON.md`
- `docs/FLOWS.md`
- `docs/WORKFLOW_COMPOSITION.md`
- `docs/API_REFERENCE.md`
