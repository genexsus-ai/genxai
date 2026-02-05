# Getting Started with GenXAI

Welcome to GenXAI - an advanced agentic AI framework with graph-based orchestration!

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/irsal2012/GenXAI.git
cd GenXAI

# Install dependencies
pip install -e ".[dev,llm]"

# Or install all optional extras
pip install -e ".[all]"

# Set up your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Your First Workflow

Create a simple agent workflow in Python:

```python
import asyncio
from genxai import Agent, AgentConfig, AgentRegistry, Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.llm.providers.openai import OpenAIProvider

async def main():
    # Create an agent
    agent_config = AgentConfig(
        role="Assistant",
        goal="Help users with their questions",
        llm_model="gpt-4",
    )
    agent = Agent(id="assistant", config=agent_config)
    
    # Register the agent and set up LLM
    AgentRegistry.register(agent)
    llm_provider = OpenAIProvider(model="gpt-4")
    # Note: wire providers into your runtime/agent as needed for your workflow
    
    # Create a graph
    graph = Graph(name="simple_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="agent", agent_id="assistant"))
    graph.add_node(OutputNode())
    
    # Connect nodes
    graph.add_edge(Edge(source="input", target="agent"))
    graph.add_edge(Edge(source="agent", target="output"))
    
    # Run the workflow
    result = await graph.run(input_data="What is AI?")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 Core Concepts

### 1. Graphs

Graphs define the workflow structure with nodes and edges:

```python
from genxai import Graph
from genxai.core.graph.nodes import InputNode, OutputNode
from genxai.core.graph.edges import Edge

graph = Graph(name="my_workflow")
graph.add_node(InputNode())
graph.add_node(OutputNode())
graph.add_edge(Edge(source="input", target="output"))
```

### 2. Agents

Agents are intelligent entities that can process tasks:

```python
from genxai import Agent, AgentConfig

config = AgentConfig(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    llm_model="gpt-4",
    temperature=0.7,
)

agent = Agent(id="analyst", config=config)
```

### 3. State Management

Manage workflow state with versioning and persistence:

```python
from genxai.core.state.manager import StateManager

state_manager = StateManager(enable_persistence=True)
state_manager.set("key", "value")
state_manager.checkpoint("important_point")
```

### 4. LLM Providers

Integrate with various LLM providers:

```python
from genxai.llm.providers.openai import OpenAIProvider

llm = OpenAIProvider(
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
)

response = await llm.generate("Hello, how are you?")
print(response.content)
```

## 📈 Metrics API (Enterprise)

The metrics API and observability endpoints are part of the enterprise edition
and live under `enterprise/`.

## 🎯 Examples

### Conditional Routing

```python
from genxai.core.graph.edges import ConditionalEdge

# Route based on state
graph.add_edge(
    ConditionalEdge(
        source="classifier",
        target="path_a",
        condition=lambda state: state.get("category") == "A"
    )
)
```

### Parallel Execution

```python
from genxai.core.graph.edges import ParallelEdge

# Execute multiple agents in parallel
graph.add_edge(ParallelEdge(source="input", target="agent1"))
graph.add_edge(ParallelEdge(source="input", target="agent2"))
```

### Agent with Tools

```python
config = AgentConfig(
    role="Research Assistant",
    goal="Research topics and provide summaries",
    tools=["web_search", "document_reader"],
    llm_model="gpt-4",
)
```

## 📖 Documentation

- [Architecture](./ARCHITECTURE.md) - System architecture and design
- [Requirements](./REQUIREMENTS.md) - Detailed requirements
- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Development roadmap
- [Tools Design](./TOOLS_DESIGN.md) - Tool system design
- [Memory Design](./MEMORY_DESIGN.md) - Memory system design

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=genxai --cov-report=html

# Run specific test file
pytest tests/unit/test_graph.py
```

## 🛠️ Development

### Project Structure

```
genxai/
├── core/           # Core components
│   ├── graph/      # Graph orchestration
│   ├── agent/      # Agent system
│   ├── state/      # State management
│   └── ...
├── llm/            # LLM providers
├── tools/          # Tool system
└── ...
```

### Code Quality

```bash
# Format code
black genxai/

# Lint code
ruff check genxai/

# Type check
mypy genxai/
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details.

## 🟢 Enterprise Edition

The Studio UI, CLI, connectors, triggers, security, and observability modules
are staged under `enterprise/` and intended for the **commercial enterprise
repository**. If you need these, extract `enterprise/` into a private repo and
add your commercial license.

## 🆘 Support

- GitHub Issues: Report bugs and request features
- Documentation: Check our comprehensive docs
- Examples: See `examples/` directory

## 🎓 Learn More

### Tutorials

1. **Basic Workflow** - Create your first agent workflow
2. **Multi-Agent System** - Build collaborative agent systems
3. **Custom Tools** - Create and integrate custom tools
4. **Memory Integration** - Add memory to your agents
5. **Production Deployment** - Deploy to production

### Advanced Topics

- Graph optimization
- Agent learning and adaptation
- Custom LLM providers
- Distributed execution
- Observability and monitoring

## 🚀 What's Next?

- Explore the [examples](./examples/) directory
- Read the [architecture documentation](./ARCHITECTURE.md)
- Join our community discussions
- Build your first AI agent workflow!

---

**Happy Building with GenXAI! 🎉**
