# GenXAI Quick Start Tutorial

**Get started with GenXAI in 5 minutes!**

---

## 📋 Prerequisites

- Python 3.11 or higher
- OpenAI API key (or other LLM provider)

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/irsal2012/GenXAI.git
cd GenXAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (core)
pip install -e ".[llm,tools]"
```

---

## 🔑 Set Up API Key

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Or add to .env file
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

---

## 🎯 Example 1: Simple Agent

Create a file `simple_agent.py`:

```python
import asyncio
import os
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

async def main():
    # Create an agent
    agent = AgentFactory.create_agent(
        id="assistant",
        role="Helpful Assistant",
        goal="Answer user questions clearly and concisely",
        llm_model="gpt-4",
        temperature=0.7,
    )

    # Create runtime
    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    
    # Execute a task
    result = await runtime.execute(
        task="Explain what an agentic AI framework is in 2 sentences."
    )
    
    print(f"Agent Response: {result['output']}")
    print(f"Tokens Used: {result['tokens_used']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Preset Agents (Assistant/UserProxy)

If you want AutoGen-style presets, use the thin wrappers:

```python
from genxai import AssistantAgent, UserProxyAgent

assistant = AssistantAgent.create(id="assistant", goal="Help the user")
user_proxy = UserProxyAgent.create(id="user_proxy", tools=["human_input"])
```

Run it:
```bash
python simple_agent.py
```

---

## 🛠️ Example 2: Agent with Tools

Create a file `agent_with_tools.py`:

```python
import asyncio
import os
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # Auto-registers all tools

async def main():
    # Create an agent with calculator tool
    agent = AgentFactory.create_agent(
        id="math_agent",
        role="Mathematics Expert",
        goal="Solve mathematical problems accurately",
        tools=["calculator"],  # Specify which tools to use
        llm_model="gpt-4",
        temperature=0.1,
    )
    
    # Get tools from registry
    calculator = ToolRegistry.get("calculator")
    
    # Create runtime
    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    runtime.set_tools({"calculator": calculator})
    
    # Execute a task
    result = await runtime.execute(
        task="Calculate: (15 * 8) + (42 / 6) - 10"
    )
    
    print(f"Agent Response: {result['output']}")
    print(f"Tokens Used: {result['tokens_used']}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python agent_with_tools.py
```

---

## 🔗 Example 3: Multi-Agent Workflow

Create a file `multi_agent_workflow.py`:

```python
import asyncio
import os
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

async def main():
    # Create agents
    researcher = AgentFactory.create_agent(
        id="researcher",
        role="Research Analyst",
        goal="Gather and analyze information",
        llm_model="gpt-4",
    )
    
    writer = AgentFactory.create_agent(
        id="writer",
        role="Content Writer",
        goal="Write clear and engaging content",
        llm_model="gpt-4",
    )
    
    # Build graph workflow
    graph = Graph(name="research_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="research_node", agent_id="researcher"))
    graph.add_node(AgentNode(id="write_node", agent_id="writer"))
    graph.add_node(OutputNode())
    
    # Add edges (sequential flow)
    graph.add_edge(Edge(source="input", target="research_node"))
    graph.add_edge(Edge(source="research_node", target="write_node"))
    graph.add_edge(Edge(source="write_node", target="output"))
    
    # Validate graph
    graph.validate()
    
    # Run workflow
    result = await graph.run(
        input_data={"topic": "Benefits of agentic AI frameworks"}
    )
    
    print(f"Workflow Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python multi_agent_workflow.py
```
Shared memory no-code workflow (OSS CLI):
```bash
genxai workflow run examples/nocode/shared_memory_workflow.yaml \
  --input '{"task": "Draft a short response"}'
```

> Note: Some templates may reference Studio-only features in enterprise builds, but
> the OSS CLI can run standard workflow YAML via `genxai workflow run`.

---

## 🔁 Example 4: Flow Orchestrators

Use the flow wrappers for common coordination patterns:

```python
import asyncio
from genxai import AgentFactory, RoundRobinFlow, SelectorFlow, P2PFlow

def choose_next(state, agent_ids):
    return agent_ids[state.get("selector_hop", 0) % len(agent_ids)]

async def main():
    agents = [
        AgentFactory.create_agent(id="analyst", role="Analyst", goal="Analyze"),
        AgentFactory.create_agent(id="writer", role="Writer", goal="Write"),
    ]

    round_robin = RoundRobinFlow(agents)
    selector = SelectorFlow(agents, selector=choose_next, max_hops=3)
    p2p = P2PFlow(agents, max_rounds=3, consensus_threshold=0.7)

    await round_robin.run({"topic": "AI adoption"})
    await selector.run({"goal": "Ship v1"})
    await p2p.run({"topic": "Decentralized coordination"})

if __name__ == "__main__":
    asyncio.run(main())
```

See runnable examples in:
- `examples/code/flow_round_robin_example.py`
- `examples/code/flow_selector_example.py`
- `examples/code/flow_p2p_example.py`
- `examples/code/flow_parallel_example.py`
- `examples/code/flow_conditional_example.py`
- `examples/code/flow_loop_example.py`
- `examples/code/flow_router_example.py`
- `examples/code/flow_ensemble_voting_example.py`
- `examples/code/flow_critic_review_example.py`
- `examples/code/flow_coordinator_worker_example.py`
- `examples/code/flow_map_reduce_example.py`
- `examples/code/flow_subworkflow_example.py`
- `examples/code/flow_auction_example.py`

---

## 🧠 Example 5: Agent with Memory

Create a file `agent_with_memory.py`:

```python
import asyncio
import os
from pathlib import Path
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.memory.manager import MemorySystem

async def main():
    # Create agent
    agent = AgentFactory.create_agent(
        id="assistant",
        role="Personal Assistant",
        goal="Remember user preferences and provide personalized help",
        llm_model="gpt-4",
        enable_memory=True,
    )
    
    # Create memory system (optionally persist to disk)
    memory = MemorySystem(
        agent_id="assistant",
        persistence_enabled=True,
        persistence_path=Path(".genxai/memory"),
    )
    
    # Create runtime with memory
    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    runtime.set_memory(memory)
    
    # First interaction
    result1 = await runtime.execute(
        task="My name is Alice and I love Python programming."
    )
    print(f"Response 1: {result1['output']}\n")
    
    # Second interaction (agent should remember)
    result2 = await runtime.execute(
        task="What's my name and what do I love?"
    )
    print(f"Response 2: {result2['output']}\n")
    
    # Check memory stats
    stats = await memory.get_stats()
    print(f"Memory Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python agent_with_memory.py
```

---

## 📊 Example 6: Check Available Tools

Create a file `list_tools.py`:

```python
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # Auto-registers all tools

# Get registry stats
stats = ToolRegistry.get_stats()

print(f"✅ Total Tools: {stats['total_tools']}")
print(f"\n📦 Tools by Category:")
for category, count in stats['categories'].items():
    print(f"  - {category}: {count} tools")

print(f"\n🔧 Available Tools:")
for tool_name in sorted(stats['tool_names']):
    tool = ToolRegistry.get(tool_name)
    print(f"  - {tool_name}: {tool.metadata.description}")
```

Run it:
```bash
python list_tools.py
```

---

## ⏰ Example 7: Trigger a Workflow (OSS Runtime)

```python
import asyncio
from genxai.triggers import ScheduleTrigger
from genxai.core.graph.trigger_runner import TriggerWorkflowRunner

runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)
trigger = ScheduleTrigger(trigger_id="daily_job", cron="0 9 * * *")

async def on_event(event):
    result = await runner.handle_event(event)
    print(result)

trigger.on_event(on_event)
await trigger.start()
```

---

## 🔌 Example 8: Connector Event Handler (OSS Runtime)

```python
from genxai.connectors import WebhookConnector

connector = WebhookConnector(connector_id="webhook_1", secret="my-secret")

async def on_event(event):
    print("Connector payload:", event.payload)

connector.on_event(on_event)
await connector.start()
```

---

## 🎨 Visualize Your Workflow

GenXAI can generate visual representations of your workflows:

```python
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge

# Create graph
graph = Graph(name="my_workflow")
graph.add_node(InputNode())
graph.add_node(AgentNode(id="agent1", agent_id="researcher"))
graph.add_node(AgentNode(id="agent2", agent_id="writer"))
graph.add_node(OutputNode())

graph.add_edge(Edge(source="input", target="agent1"))
graph.add_edge(Edge(source="agent1", target="agent2"))
graph.add_edge(Edge(source="agent2", target="output"))

# Print ASCII visualization
print(graph.draw_ascii())

# Generate Mermaid diagram
print(graph.to_mermaid())

# Generate GraphViz DOT format
print(graph.to_dot())
```

---

## 🧪 Run Tests

```bash
# Run all unit tests
python -m pytest tests/unit -v

# Run with coverage
python -m pytest tests/unit --cov=genxai --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 📚 Next Steps

### Learn More
- Read [ARCHITECTURE.md](../ARCHITECTURE.md) for system design
- Check [examples/](../examples/) for more examples
- See [docs/](../docs/) for detailed documentation
- Explore [no-code templates](../examples/nocode/README.md) (including shared agents in `examples/nocode/agents/`)
- Try the shared memory template: `examples/nocode/shared_memory_workflow.yaml`
- Run [benchmarks](./BENCHMARKING.md)

### Explore Features
- **Graph Patterns**: See `examples/patterns/` for workflow patterns
- **Tool Creation**: Read `TOOLS_DESIGN.md` to create custom tools
- **Memory System**: Explore `MEMORY_DESIGN.md` for advanced memory features
- **LLM Integration**: Check `docs/LLM_INTEGRATION.md` for provider setup

### Build Your Own
1. **Custom Agents**: Extend `Agent` class for specialized behavior
2. **Custom Tools**: Implement `Tool` interface for new capabilities
3. **Custom Workflows**: Design complex graphs with conditional routing
4. **Custom Memory**: Implement custom memory stores

---

## 🐛 Troubleshooting

### Issue: "No LLM provider available"
**Solution**: Set your API key:
```bash
export OPENAI_API_KEY="sk-your-key"
```

### Issue: "Tool not found in registry"
**Solution**: Import tools to register them:
```python
from genxai.tools.builtin import *
```

### Issue: "Module not found"
**Solution**: Install with dependencies:
```bash
pip install -e ".[llm,tools]"
```

### Issue: Tests failing
**Solution**: Check Python version (3.11+):
```bash
python --version
```

---

## 💡 Tips & Best Practices

1. **Start Simple**: Begin with a single agent, then add complexity
2. **Use Tools**: Leverage the built-in tools before creating custom ones
3. **Enable Memory**: Add memory for context-aware agents
4. **Validate Graphs**: Always call `graph.validate()` before running
5. **Monitor Tokens**: Track token usage to manage costs
6. **Test Locally**: Use small models (gpt-3.5-turbo) for development
7. **Handle Errors**: Wrap agent execution in try-except blocks
8. **Set Timeouts**: Use `timeout` parameter to prevent hanging

---

## 🎉 Success!

You've completed the GenXAI quick start tutorial! You now know how to:
- ✅ Create agents with different roles
- ✅ Use built-in tools
- ✅ Build multi-agent workflows
- ✅ Add memory to agents
- ✅ Visualize workflows
- ✅ Run tests

### What's Next?

Explore the [examples/](../examples/) directory for more advanced use cases:
- Sequential patterns
- Conditional branching
- Parallel execution
- Coordinator-delegator-worker pattern
- Cyclic/iterative workflows
- Peer-to-peer collaboration

---

## 📞 Get Help

- **Documentation**: Check [docs/](../docs/) directory
- **Examples**: Browse [examples/](../examples/) directory
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord (coming soon!)

---

**Happy Building! 🚀**

*GenXAI - Advanced Agentic AI Framework*
