# GenXAI API Reference (Quick Guide)

This guide provides a condensed view of the GenXAI API. For the complete
reference and examples, see `docs/API_REFERENCE.md`.

---

## Core Concepts

- **Agents**: configured with roles, goals, LLM providers, tools, memory
- **Graphs**: define execution flow with nodes and edges
- **Flows**: orchestration helpers for common patterns
- **Tools**: registered capabilities available to agents

---

## Agent Basics

```python
from genxai.core.agent import AgentFactory

agent = AgentFactory.create_agent(
    id="assistant",
    role="Assistant",
    goal="Help users",
    llm_model="gpt-4",
)
```

Run a task:

```python
from genxai.core.agent.runtime import AgentRuntime

runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
result = await runtime.execute(task="Summarize this text")
```

---

## Graph Execution

```python
from genxai.core.graph import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge

graph = Graph(name="simple")
graph.add_node(InputNode())
graph.add_node(AgentNode(id="agent", agent_id="assistant"))
graph.add_node(OutputNode())
graph.add_edge(Edge(source="input", target="agent"))
graph.add_edge(Edge(source="agent", target="output"))

graph.validate()
result = await graph.run(input_data={"text": "Hello"})
```

---

## Flow Orchestrators

```python
from genxai import AgentFactory, RoundRobinFlow

agents = [
    AgentFactory.create_agent(id="a1", role="Analyst", goal="Analyze"),
    AgentFactory.create_agent(id="a2", role="Writer", goal="Write"),
]

flow = RoundRobinFlow(agents)
result = await flow.run({"topic": "AI"})
```

---

## Tool Registry

```python
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # auto-registers built-in tools

stats = ToolRegistry.get_stats()
calculator = ToolRegistry.get("calculator")
```

---

## Where to Go Next

- Full API reference: `docs/API_REFERENCE.md`
- Workflow patterns: `docs/FLOWS.md`
- Tool system design: `TOOLS_DESIGN.md`

