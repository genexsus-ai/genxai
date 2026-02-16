# CrewAI vs GenXAI — Comparison Guide

This document explains how CrewAI concepts (agents + tasks) map to GenXAI
concepts (agents + workflows/graphs/flows), with concrete examples and
implementation guidance.

---

## 1) Concept Mapping (High-Level)

| CrewAI Concept | GenXAI Equivalent | Notes |
|---|---|---|
| **Agent** | **Agent** | Same idea. Use `AgentFactory.create_agent(...)`. |
| **Task** | **Workflow step (Graph node)** | Each CrewAI task becomes a node in a GenXAI graph. |
| **Task description** | **Runtime task input** | Passed via `AgentRuntime.execute(task=...)` or `graph.run(input_data=...)`. |
| **Task expected_output** | **Agent goal + validation** | Put desired format in `Agent.goal`, enforce via validation nodes/loops. |
| **Task order/dependencies** | **Edges / Conditions / Loops** | Orchestrated via edges, conditional nodes, and loops. |
| **Multiple tasks for one agent** | **Same agent reused across nodes** | Same agent ID can appear in multiple steps. |

---

## 1.1) CrewAI Pattern → GenXAI Mapping

| CrewAI Pattern | GenXAI Equivalent |
|---|---|
| **Sequential** | `RoundRobinFlow` or graph edges |
| **Parallel** | `ParallelFlow` or parallel edges |
| **Hierarchical** | `CoordinatorWorkerFlow` or `SubworkflowFlow` |
| **Hybrid** | Combine sequential + parallel + conditional in one graph |
| **Async** | Native `async/await` across `AgentRuntime` + `Graph.run` |

---

## 2) CrewAI Example (Tasks)

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Researcher",
    goal="Find reliable sources",
)

writer = Agent(
    role="Writer",
    goal="Write a concise summary",
)

research_task = Task(
    description="Research recent AI adoption in healthcare",
    agent=researcher,
    expected_output="A list of 5 reputable sources with summaries"
)

write_task = Task(
    description="Write a 2-paragraph summary of AI adoption",
    agent=writer,
    expected_output="Concise summary with citations"
)

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
result = crew.kickoff()
```

---

## 3) GenXAI Equivalent (Python Graph)

Below is the GenXAI translation showing **task description** and
**expected output** handling.

```python
from genxai import AgentFactory, Graph
from genxai.core.graph.nodes import InputNode, AgentNode, ConditionNode, OutputNode
from genxai.core.graph.edges import Edge, ConditionalEdge

# 1) Agents (goal = expected_output guidance)
researcher = AgentFactory.create_agent(
    id="researcher",
    role="Researcher",
    goal="Return a list of 5 reputable sources with short summaries",
)

writer = AgentFactory.create_agent(
    id="writer",
    role="Writer",
    goal="Write a concise 2-paragraph summary with citations",
)

# 2) Validation functions (expected_output enforcement)
def research_ok(state):
    text = state.get("output", "")
    return text.count("http") >= 5  # naive: 5 sources

def writing_ok(state):
    text = state.get("output", "")
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    return len(paragraphs) >= 2 and "http" in text

# 3) Graph = tasks + dependencies
graph = Graph(name="crewai_task_equivalent")

graph.add_node(InputNode(id="input"))
graph.add_node(AgentNode(id="research_task", agent_id=researcher.id))
graph.add_node(ConditionNode(id="research_validate", condition="research_ok"))

graph.add_node(AgentNode(id="write_task", agent_id=writer.id))
graph.add_node(ConditionNode(id="write_validate", condition="writing_ok"))

graph.add_node(OutputNode(id="output"))

# Task 1
graph.add_edge(Edge("input", "research_task"))
graph.add_edge(Edge("research_task", "research_validate"))
graph.add_edge(ConditionalEdge("research_validate", "write_task", lambda s: research_ok(s)))
graph.add_edge(ConditionalEdge("research_validate", "research_task", lambda s: not research_ok(s)))

# Task 2
graph.add_edge(Edge("write_task", "write_validate"))
graph.add_edge(ConditionalEdge("write_validate", "output", lambda s: writing_ok(s)))
graph.add_edge(ConditionalEdge("write_validate", "write_task", lambda s: not writing_ok(s)))

# CrewAI Task.description equivalent → runtime input
result = await graph.run(input_data={
    "task": "Research AI adoption in healthcare, then write a 2-paragraph summary with citations"
})
```

---

## 4) GenXAI Equivalent (YAML Workflow)

```yaml
workflow:
  name: "CrewAI Task Translation"
  description: "Research → Write with validation loops"

  agents:
    - id: "researcher"
      role: "Researcher"
      goal: "Return a list of 5 reputable sources with short summaries"

    - id: "writer"
      role: "Writer"
      goal: "Write a concise 2-paragraph summary with citations"

  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "research_task"
        type: "agent"
        agent: "researcher"
      - id: "write_task"
        type: "agent"
        agent: "writer"
      - id: "end"
        type: "output"

    edges:
      - from: "start"
        to: "research_task"
      - from: "research_task"
        to: "write_task"
      - from: "write_task"
        to: "end"
```

> For validation/expected output enforcement in YAML, add a condition/loop node
> or introduce a critic agent that checks formatting and loops back if needed.

---

## 5) Additional Examples

### Example A — One Agent, Multiple Tasks (Reuse Agent Across Nodes)

CrewAI allows one agent to handle multiple tasks. In GenXAI, you **reuse the same
agent ID** across multiple workflow nodes.

```python
from genxai import AgentFactory, Graph
from genxai.core.graph.nodes import InputNode, AgentNode, OutputNode
from genxai.core.graph.edges import Edge

researcher = AgentFactory.create_agent(
    id="researcher",
    role="Researcher",
    goal="Research and summarize",
)

graph = Graph(name="same_agent_multiple_tasks")
graph.add_node(InputNode(id="input"))
graph.add_node(AgentNode(id="research_task", agent_id=researcher.id))
graph.add_node(AgentNode(id="summary_task", agent_id=researcher.id))
graph.add_node(OutputNode(id="output"))

graph.add_edge(Edge("input", "research_task"))
graph.add_edge(Edge("research_task", "summary_task"))
graph.add_edge(Edge("summary_task", "output"))
```

---

### Example B — Flow Orchestrator (Quick Task Patterns)

If your CrewAI tasks are mostly sequential or patterned, use a **Flow** to avoid
manual graph wiring.

```python
from genxai import AgentFactory, RoundRobinFlow

agents = [
    AgentFactory.create_agent(id="planner", role="Planner", goal="Plan"),
    AgentFactory.create_agent(id="writer", role="Writer", goal="Write"),
]

flow = RoundRobinFlow(agents)
result = await flow.run({"topic": "AI adoption"})
```

---

### Example C — Runtime Execute (Task.description Equivalent)

If you want a very direct mapping to `Task.description`, call the agent runtime
multiple times with different `task=` values.

```python
from genxai.core.agent.runtime import AgentRuntime

runtime = AgentRuntime(agent=researcher, api_key="...")

r1 = await runtime.execute(task="Research recent AI adoption in healthcare")
r2 = await runtime.execute(task="Summarize the findings in 2 paragraphs")
```

---

### Example D — Expected Output via Critic Loop

Use a **CriticReviewFlow** to enforce output quality (CrewAI expected_output).

```python
from genxai import AgentFactory, CriticReviewFlow

writer = AgentFactory.create_agent(
    id="writer",
    role="Writer",
    goal="Write a concise summary with citations",
)

critic = AgentFactory.create_agent(
    id="critic",
    role="Critic",
    goal="Approve only if output has 2 paragraphs and citations",
)

flow = CriticReviewFlow([writer, critic], max_iterations=3)
result = await flow.run({"topic": "AI adoption in healthcare"})
```

---

### Example E — Conditional Routing (If/Else Task Assignment)

CrewAI tasks sometimes branch based on input. In GenXAI, use a condition node
or a `RouterFlow`/`ConditionalFlow`.

```python
from genxai import AgentFactory, ConditionalFlow

agents = [
    AgentFactory.create_agent(id="analyst", role="Analyst", goal="Handle priority"),
    AgentFactory.create_agent(id="reviewer", role="Reviewer", goal="Handle normal"),
]

def choose_agent(state):
    return "analyst" if state.get("priority") == "high" else "reviewer"

flow = ConditionalFlow(agents, condition=choose_agent)
result = await flow.run({"priority": "high"})
```

---

### Example F — Parallel Tasks (Fan-Out/Fan-In)

Run multiple tasks simultaneously (e.g., parallel research) using `ParallelFlow`.

```python
from genxai import AgentFactory, ParallelFlow

agents = [
    AgentFactory.create_agent(id="source_a", role="Researcher", goal="Find sources A"),
    AgentFactory.create_agent(id="source_b", role="Researcher", goal="Find sources B"),
]

flow = ParallelFlow(agents)
result = await flow.run({"topic": "AI adoption"})
```

---

### Example G — Subworkflow Composition (Reusable Task Groups)

Use `SubworkflowFlow` or `SubgraphNode` to embed reusable task groups in a
larger workflow.

```python
from genxai import Graph, SubworkflowFlow
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge

subgraph = Graph(name="research_subflow")
subgraph.add_node(InputNode(id="input"))
subgraph.add_node(AgentNode(id="researcher", agent_id="researcher"))
subgraph.add_node(OutputNode(id="output"))
subgraph.add_edge(Edge("input", "researcher"))
subgraph.add_edge(Edge("researcher", "output"))

subflow = SubworkflowFlow(subgraph)
result = await subflow.run({"topic": "AI adoption"})
```

---

### Example H — Map-Reduce / Coordinator-Worker

These flows represent complex task decomposition and aggregation patterns.

```python
from genxai import AgentFactory, MapReduceFlow, CoordinatorWorkerFlow

map_reduce = MapReduceFlow([
    AgentFactory.create_agent(id="mapper1", role="Mapper", goal="Process shard"),
    AgentFactory.create_agent(id="mapper2", role="Mapper", goal="Process shard"),
    AgentFactory.create_agent(id="reducer", role="Reducer", goal="Aggregate results"),
])

coord_worker = CoordinatorWorkerFlow([
    AgentFactory.create_agent(id="coordinator", role="Coordinator", goal="Plan tasks"),
    AgentFactory.create_agent(id="worker", role="Worker", goal="Execute tasks"),
])

mr_result = await map_reduce.run({"data": "sharded input"})
cw_result = await coord_worker.run({"task": "Launch campaign"})
```

---

### Example I — Loop / Iterative Refinement

For iterative tasks (e.g., refine until a condition is met), use `LoopFlow` or
loop edges in a graph.

```python
from genxai import AgentFactory, LoopFlow

agents = [
    AgentFactory.create_agent(id="refiner", role="Refiner", goal="Improve the draft"),
]

flow = LoopFlow(agents, condition_key="done", max_iterations=3)
result = await flow.run({"done": False, "topic": "AI adoption"})
```

---

### Example J — Auction Flow (Agents Bid for Task)

Use `AuctionFlow` when multiple agents compete to take a task.

```python
from genxai import AgentFactory, AuctionFlow

agents = [
    AgentFactory.create_agent(id="bidder1", role="Bidder", goal="Bid to handle task"),
    AgentFactory.create_agent(id="bidder2", role="Bidder", goal="Bid to handle task"),
]

flow = AuctionFlow(agents)
result = await flow.run({"task": "Handle customer escalation"})
```

---

### Example K — Deterministic Tool Nodes (Non-Agent Steps)

GenXAI workflows can mix AI steps with deterministic tool steps.

```python
from genxai import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode, ToolNode
from genxai.core.graph.edges import Edge

graph = Graph(name="tool_augmented_flow")
graph.add_node(InputNode(id="input"))
graph.add_node(ToolNode(id="read_file", tool_name="file_reader"))
graph.add_node(AgentNode(id="summarizer", agent_id="writer"))
graph.add_node(OutputNode(id="output"))

graph.add_edge(Edge("input", "read_file"))
graph.add_edge(Edge("read_file", "summarizer"))
graph.add_edge(Edge("summarizer", "output"))
```

---

## 6) FAQ

### Q: Can one agent do multiple tasks like in CrewAI?
**Yes.** In GenXAI you reuse the **same agent ID** across multiple graph nodes.

### Q: Where is `expected_output` defined in GenXAI?
It’s implemented through:
- **Agent goal** (prompting the format), and
- **Workflow validation** (ConditionNode, critic loop, or schema checks).

### Q: Where is `Task.description` defined?
It’s passed at runtime in `input_data` or as the `task` argument when executing an agent.

---

## 7) Which One Is Better?

**Honest answer:** it depends on your needs.

- **Choose CrewAI** if you want a simpler task-first API and mostly sequential
  multi-agent workflows with minimal orchestration complexity.
- **Choose GenXAI** if you need **graph-based orchestration**, advanced memory,
  tool registry and schema-based calling, event-driven triggers/connectors, and
  enterprise-grade runtime features.

If you share your use case (workflow complexity, integrations, team size),
we can give a direct recommendation.

---

## 8) Platform Capabilities Comparison (Beyond Tasks)

### Memory (State & Context)

- **CrewAI:** Typically uses task prompts and agent backstory; memory is external or custom.
- **GenXAI:** Built-in memory system (short-term, long-term, episodic, semantic).

```python
from genxai.core.memory.manager import MemorySystem

memory = MemorySystem(agent_id="assistant", persistence_enabled=True)
await memory.add_to_short_term({"preference": "likes summaries"})
context = await memory.get_short_term_context()
```

---

### Tool Registry & Tool Calling

- **CrewAI:** Tools usually attached directly to agents.
- **GenXAI:** Central tool registry + schema-based calling.

```python
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # registers built-in tools

calculator = ToolRegistry.get("calculator")
tools = {"calculator": calculator}
runtime.set_tools(tools)
```

---

### Triggers & Connectors (Event-Driven Workflows)

- **CrewAI:** Generally manual kickoff or custom integration.
- **GenXAI:** Built-in triggers/connectors (webhooks, schedules, Kafka, etc.).

```python
from genxai.triggers import WebhookTrigger

trigger = WebhookTrigger(trigger_id="support_webhook", secret="my-secret")
trigger.on_event(lambda event: print(event.payload))
await trigger.start()
```

---

### Observability (Metrics/Tracing)

- **CrewAI:** Typically custom logging.
- **GenXAI:** Built-in metrics + tracing hooks.

```python
from genxai.observability.tracing import span

with span("genxai.agent.execute", {"agent_id": "researcher"}):
    result = await runtime.execute("...")
```

---

### Usage & Cost Tracking

- **GenXAI usage**: token usage is automatically tracked per agent; Prometheus
  metrics are available via `genxai metrics serve`.
- **Cost tracking**: detailed cost analysis per agent/task is **roadmapped**
  (see `docs/LLM_INTEGRATION.md`).

---

## References

- `docs/FLOWS.md`
- `docs/WORKFLOW_COMPOSITION.md`
- `docs/WORKFLOW_EXECUTION.md`
- `docs/API_REFERENCE.md`
