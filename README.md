# GenXAI - Advanced Agentic AI Framework

**Version:** 0.1.4  
**Status:** Active Development  
**License:** MIT

---

## 🚀 Overview

GenXAI is an advanced agentic AI framework designed to surpass existing solutions (CrewAI, AutoGen, BeeAI, n8n) by combining:

- **Graph-Based Orchestration** (like LangGraph) for complex agent workflows
- **Advanced Memory Systems** with multiple memory types (short-term, long-term, episodic, semantic, procedural)
- **No-Code Studio (Enterprise)** for visual workflow building
- **50+ Built-in Tools** for web, database, file, computation, and communication tasks
- **Enterprise Features** including observability, security, and scalability

> **Open Source vs Enterprise**: This repository contains the **MIT-licensed core framework**. The
> enterprise Studio and related enterprise features have been moved to `enterprise/` as a staging
> area for a separate commercial repo.

## ✅ OSS vs Enterprise

**Open-source (MIT) core** — use these for OSS releases:
- `genxai/` (agents, graph engine, flows, tools, LLM providers)
- `examples/`, `docs/`, `tests/`, `scripts/`

**Enterprise (commercial) features** — keep in the enterprise repo:
- `enterprise/` (Studio UI/backend, CLI, connectors, triggers, security, observability, metrics)

---

## ✨ Key Features

### 🔗 Graph-Based Workflows
- Define complex agent relationships as directed graphs
- Conditional edges and dynamic routing
- Parallel and sequential execution
- Cycles, loops, and subgraphs
- Real-time visualization

### 🧠 Advanced Agent Capabilities
- **Multi-Modal**: Text, vision, audio, code understanding
- **Learning**: Self-improvement through feedback
- **Memory**: Multi-layered memory system
- **Tools**: 50+ built-in tools + custom tool creation
- **Personality**: Configurable agent personalities

### 💾 Multi-Layered Memory
- **Short-Term**: Recent conversation context
- **Long-Term**: Persistent knowledge with vector search
- **Episodic**: Past experiences and learning
- **Semantic**: Factual knowledge base
- **Procedural**: Learned skills and procedures
- **Working**: Active processing space

### 🎨 No-Code Studio
The Studio UI and enterprise backend are now staged under:

```
enterprise/studio/
```

They are intended for the **enterprise repo** and are **not part of the MIT-licensed core**.

### ⚡ Trigger SDK (Enterprise)
Trigger SDKs are part of the enterprise edition and live under `enterprise/`.

### 🏢 Enterprise-Ready (Enterprise Edition)
- **Observability**: Logging, metrics, tracing
- **Security**: RBAC, encryption, guardrails
- **Scalability**: Horizontal scaling, distributed execution
- **Reliability**: 99.9% uptime target

### 📈 Metrics API (Enterprise)
Observability endpoints are part of the enterprise edition and live under `enterprise/`.

---

## 📋 Documentation

Comprehensive documentation is available in the following files:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture and design principles
- **[REQUIREMENTS.md](./REQUIREMENTS.md)** - Detailed functional and non-functional requirements
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[TOOLS_DESIGN.md](./TOOLS_DESIGN.md)** - Tool system architecture and 50+ built-in tools
- **[MEMORY_DESIGN.md](./MEMORY_DESIGN.md)** - Multi-layered memory system design

---

## 🎯 Design Goals

1. **Superior to Existing Frameworks**: More features than CrewAI, AutoGen, BeeAI
2. **Graph-First**: Complex orchestration like LangGraph, but better
3. **No-Code Friendly**: Visual interface for non-technical users
4. **Enterprise-Grade**: Production-ready with observability and security
5. **Extensible**: Plugin architecture for easy customization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  No-Code Studio  │  │   CLI/SDK/API    │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Graph Engine │  │ Flow Control │  │ State Manager│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Agent Runtime│  │ Memory System│  │ Tool Registry│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete details.

---

## 💡 Quick Start

### Using GenXAI as a Framework Library

```python
import os
from genxai import Agent, AgentConfig, AgentRegistry, Graph

# Set your API key (required)
os.environ["OPENAI_API_KEY"] = "sk-your-api-key-here"

# Define agents
classifier = Agent(
    id="classifier",
    config=AgentConfig(
        role="Classifier",
        goal="Categorize customer requests",
        llm_model="gpt-4",
        tools=["sentiment_analysis", "category_detector"],
    ),
)

support = Agent(
    id="support",
    config=AgentConfig(
        role="Support Agent",
        goal="Resolve customer issues",
        llm_model="claude-3-opus",
        enable_memory=True,
    ),
)

AgentRegistry.register(classifier)
AgentRegistry.register(support)

# Build graph
graph = Graph()
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge

graph.add_node(InputNode(id="start"))
graph.add_node(AgentNode(id="classify", agent_id="classifier"))
graph.add_node(AgentNode(id="support", agent_id="support"))
graph.add_node(OutputNode(id="end"))

graph.add_edge(Edge(source="start", target="classify"))
graph.add_edge(Edge(source="classify", target="support"))
graph.add_edge(Edge(source="support", target="end"))

# Run workflow
result = await graph.run(input_data="My app crashed")
```

### Flow Orchestrator Examples

GenXAI also ships with lightweight flow orchestrators for common patterns:

```python
from genxai import AgentFactory, RoundRobinFlow, SelectorFlow, P2PFlow

agents = [
    AgentFactory.create_agent(id="analyst", role="Analyst", goal="Analyze"),
    AgentFactory.create_agent(id="writer", role="Writer", goal="Write"),
]

# Round-robin flow
round_robin = RoundRobinFlow(agents)

# Selector flow
def choose_next(state, agent_ids):
    return agent_ids[state.get("selector_hop", 0) % len(agent_ids)]

selector = SelectorFlow(agents, selector=choose_next, max_hops=3)

# P2P flow
p2p = P2PFlow(agents, max_rounds=4, consensus_threshold=0.7)
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

Full flow documentation: [docs/FLOWS.md](./docs/FLOWS.md)

### Trigger SDK Quick Start (Enterprise)

> This example requires the enterprise repository.

```python
from genxai.triggers import WebhookTrigger
from genxai.core.graph import TriggerWorkflowRunner

trigger = WebhookTrigger(trigger_id="support_webhook", secret="my-secret")

# Wire trigger to workflow
runner = TriggerWorkflowRunner(nodes=nodes, edges=edges)

async def on_event(event):
    result = await runner.handle_event(event)
    print("Workflow result:", result)

trigger.on_event(on_event)
await trigger.start()

# In your FastAPI handler:
# await trigger.handle_request(payload, raw_body=raw, headers=request.headers)
```

### Install Options

```bash
# Core install
pip install genxai-framework

# Full install with providers/tools (core)
pip install "genxai-framework[llm,tools]"

# Everything included
pip install "genxai-framework[all]"
```

> For the enterprise Studio, use the enterprise repository and its commercial license.

---

## 🛠️ Technology Stack

### Core Framework
- **Language**: Python 3.11+
- **Validation**: Pydantic v2
- **Concurrency**: AsyncIO
- **Testing**: Pytest

### Storage
- **Metadata**: PostgreSQL
- **Caching**: Redis
- **Vector DB**: Pinecone, Weaviate, Chroma
- **Graph DB**: Neo4j

### LLM Providers
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3)
- Google (Gemini)
- Cohere
- Local models (Ollama, LM Studio)

### No-Code Studio
- **Frontend**: React + TypeScript
- **Graph Viz**: ReactFlow
- **Styling**: TailwindCSS
- **Backend**: FastAPI

### DevOps
- **Containers**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana

---

## 🎯 Key Differentiators

### vs CrewAI
✅ Graph-based workflows (not just sequential)  
✅ Advanced memory system  
✅ No-code interface  
✅ Learning agents  
✅ Enterprise features

### vs AutoGen
✅ Simpler configuration  
✅ Rich built-in tools  
✅ Visual workflow builder  
✅ Better state management  
✅ Multi-modal support

### vs BeeAI
✅ More sophisticated agents  
✅ Complex orchestration  
✅ Advanced memory  
✅ Enterprise scalability  
✅ Comprehensive tooling

### vs LangGraph
✅ All graph features PLUS:  
✅ No-code interface  
✅ Advanced agent capabilities  
✅ Multi-layered memory  
✅ Tool marketplace  
✅ Learning and adaptation

---

## 📊 Success Metrics

### Technical
- ✅ All functional requirements implemented
- ✅ 80%+ test coverage
- ✅ 99.9% uptime
- ✅ < 2s agent response time

### Business
- 🎯 10,000+ GitHub stars in first year
- 🎯 100+ contributors
- 🎯 100+ companies in production
- 🎯 4.5+ star rating

### User Experience
- 🎯 < 5 minutes to first workflow
- 🎯 Non-technical users productive in < 1 hour
- 🎯 < 5% framework-related failures

---

## 🤝 Contributing

We welcome contributions! This project is in active development. We provide:

- Contributing guidelines
- Development setup instructions
- Issue templates
- Pull request templates

---

## 📜 License

MIT License

---

## 🔗 Links

- **Documentation**: See docs/ directory
- **GitHub**: (To be created)
- **Discord**: (To be created)
- **Website**: (To be created)

---

## 📧 Contact

For questions or collaboration opportunities, please reach out through GitHub Discussions (once created).

---

## 🙏 Acknowledgments

Inspired by:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Graph-based orchestration
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent collaboration
- [AutoGen](https://github.com/microsoft/autogen) - Conversational agents
- [BeeAI](https://github.com/i-am-bee/bee-agent-framework) - Agent framework design

---

## 📈 Project Status

**Current Phase**: Active Development  
**Next Milestone**: Complete visual editor + studio polish  
**Expected Launch**: TBD

---

**Built with ❤️ by the GenXAI team**
