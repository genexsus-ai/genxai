# CrewAI vs GenXAI — Slide Outline

Use this outline to create a slide deck quickly.

---

## Slide 1 — Title
- **CrewAI vs GenXAI**
- Task/Agent mapping + orchestration patterns

---

## Slide 2 — Concept Mapping
- CrewAI **Agent** → GenXAI **Agent**
- CrewAI **Task** → GenXAI **Workflow Node**
- `Task.description` → runtime input
- `Task.expected_output` → agent goal + validation loop

---

## Slide 2.1 — CrewAI Pattern Mapping
- Sequential → `RoundRobinFlow` / graph edges
- Parallel → `ParallelFlow`
- Hierarchical → `CoordinatorWorkerFlow` / subworkflow
- Hybrid → mix sequential/parallel/conditional
- Async → native `async/await`

---

## Slide 3 — Task Example (CrewAI)
- Research + Write tasks
- Expected outputs on each task

---

## Slide 4 — Task Example (GenXAI Graph)
- AgentNode per task
- ConditionNode for expected output
- Edges for ordering + loops

---

## Slide 5 — Reuse One Agent for Many Tasks
- Same agent ID reused across multiple nodes

---

## Slide 6 — Flow Orchestrators
- `RoundRobinFlow`, `ParallelFlow`, `ConditionalFlow`
- `LoopFlow`, `CriticReviewFlow`, `AuctionFlow`

---

## Slide 7 — Advanced Patterns
- Subworkflow composition
- Map-Reduce / Coordinator-Worker

---

## Slide 8 — Expected Output Enforcement
- Goal/prompt (soft)
- Validation node (hard)
- Critic loop (hard)

---

## Slide 9 — Beyond Tasks
- Memory system
- Tool registry + schema calling
- Triggers/connectors
- Observability (metrics/tracing)

---

## Slide 10 — Which One Is Better?
- **CrewAI**: simpler task-first API, sequential workflows
- **GenXAI**: graph orchestration, advanced memory/tools, enterprise runtime

---

## Slide 11 — Usage & Cost Tracking
- **Usage**: token tracking per agent + metrics API
- **Cost**: detailed cost tracking per agent/task is on the roadmap

---

## Slide 12 — References
- `docs/COMPARISON.md`
- `docs/COMPARISON_CHEATSHEET.md`
- `docs/FLOWS.md`
- `docs/WORKFLOW_COMPOSITION.md`
