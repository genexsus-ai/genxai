# GenXAI - Advanced Agentic AI Framework

**Version:** 1.0.0  
**Status:** Active Development  
**License:** MIT
# Irsal Imran - [irsal2025@gmail.com](mailto:irsal2025@gmail.com)
---

## 🚀 Overview

GenXAI is an advanced agentic AI framework designed to surpass existing solutions by combining:

- **Graph-Based Orchestration** (like LangGraph) for complex agent workflows
- **Advanced Memory Systems** with multiple memory types (short-term, long-term, episodic, semantic, procedural)
- **No-Code Studio (Enterprise)** for visual workflow building
- **50+ Built-in Tools** for web, database, file, computation, and communication tasks
- **Enterprise-Grade Features (OSS)** including observability, security, connectors, and scalability

> **Open Source vs Enterprise**: This repository contains the **MIT-licensed core framework** plus
> enterprise-grade runtime features (connectors, triggers, observability, security, CLI extensions).
> The **Studio UI** is planned as an enterprise-only product in a separate commercial repository;
> its code is not included in this repository.

## 🧩 Applications

- **[Autonomous Coding Agent](https://github.com/genexsus-ai/genxbot/blob/main/README.md)**: GenXAI-powered autonomous coding application.
  - Includes recipe-template run support with blended recipe + agent-generated actions (dedupe + fallback action coverage), plus structured observability hooks for planning latency, tool invocations, safety decisions, and retry/failure events.
- **[AI Strategy Agent (P2P Brainstorming)](./applications/ai_strategy_agent/backend/README.md)**: peer-to-peer brainstorming workflow with layered architecture and local observability hooks.
- **[Travel Planning Agent](./applications/travel_planning_agent/README.md)**: GenXAI-powered travel planning app with FastAPI backend, React frontend, and streaming itinerary updates.

## ✅ OSS vs Enterprise

**Open-source (MIT) core + enterprise-grade runtime** — available in OSS:
- `genxai/` (agents, graph engine, flows, tools, LLM providers)
- `genxai/connectors` (Kafka, SQS, Postgres CDC, webhooks, Slack, GitHub, Jira, Notion, Google Workspace)
- `genxai/triggers` (webhook, schedule, queue triggers)
- `genxai/observability` (logging, metrics, tracing)
- `genxai/security` (RBAC, policy engine, audit, rate limits)
- CLI commands: `tool`, `workflow`, `connector`, `metrics`, `approval`, `audit`
- `examples/`, `docs/`, `tests/`, `scripts/`

**Enterprise (commercial) features** — planned for a separate commercial repository:
- Studio UI/backend + Studio-only assets (not included in this repository)

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
- **LLM Ranking (opt-in)**: Safe JSON-based ranking with heuristic fallbacks for tool selection ([docs/LLM_INTEGRATION.md](./docs/LLM_INTEGRATION.md))

> **New in 0.1.6:** LLM ranking utility for tool selection with safe JSON parsing and heuristic fallbacks. See [LLM integration](./docs/LLM_INTEGRATION.md).

### 💾 Multi-Layered Memory
- **Short-Term**: Recent conversation context
- **Long-Term**: Persistent knowledge with vector search
- **Episodic**: Past experiences and learning
- **Semantic**: Factual knowledge base
- **Procedural**: Learned skills and procedures
- **Working**: Active processing space
- **Backend Plugins (Implemented)**: Redis, SQLite, Neo4j via formal plugin registry
- **Telemetry (Implemented)**: Backend memory utilization, size, and graph traversal metrics via `MemorySystem.get_stats()`

```python
stats = await memory.get_stats()
print(stats["backend_plugins"].keys())  # e.g. redis/sqlite/neo4j (when configured)
```

### 🎨 No-Code Studio
The Studio UI and its backend are **planned** as an enterprise-only product in a separate
commercial repository. They are **not part of the MIT-licensed core** and are not included
in this repository.

### ⚡ Trigger SDK (OSS)
Trigger SDKs are part of the OSS runtime and live under `genxai/triggers`.

### 🏢 Enterprise-Ready (OSS Runtime)
- **Observability**: Logging, metrics, tracing
- **Security**: RBAC, encryption, guardrails
- **Scalability**: Horizontal scaling, distributed execution
- **Reliability**: 99.9% uptime target

### 📈 Metrics API (OSS Runtime)
Observability endpoints are part of the OSS runtime and live under `genxai/observability`.

---

## 📋 Documentation

Comprehensive documentation is available in the following files:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system architecture and design principles
- **[REQUIREMENTS.md](./REQUIREMENTS.md)** - Detailed functional and non-functional requirements
- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Development roadmap
- **[TOOLS_DESIGN.md](./TOOLS_DESIGN.md)** - Tool system architecture and 50+ built-in tools
- **[MEMORY_DESIGN.md](./MEMORY_DESIGN.md)** - Multi-layered memory system design
- **[WORKFLOW_COMPOSITION.md](./docs/WORKFLOW_COMPOSITION.md)** - Composing global workflows with subflows
- **[COMPARISON.md](./docs/COMPARISON.md)** - CrewAI vs GenXAI comparison guide
- **[COMPARISON_CHEATSHEET.md](./docs/COMPARISON_CHEATSHEET.md)** - Condensed comparison cheatsheet
- **[COMPARISON_SLIDES.md](./docs/COMPARISON_SLIDES.md)** - Slide-style outline for presentations

### 🖼️ Workflow Composition Preview

For a visual overview of composing global workflows with subflows and deterministic routing,
see **[docs/WORKFLOW_COMPOSITION.md](./docs/WORKFLOW_COMPOSITION.md)**.

![Workflow composition diagram](./docs/diagrams/workflow_composition.svg)

_Figure: Global workflow routing to two subflows (SVG preview)._ 

![Workflow composition diagram (PNG)](./docs/diagrams/workflow_composition.png)

_Figure: PNG preview for environments that don’t render SVG._

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
│                    PRESENTATION LAYER                       │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  No-Code Studio  │  │   CLI/SDK/API    │                 │
│  │  (Visual Editor) │  │  (Code Interface)│                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Graph Engine │  │ Flow Control │  │ State Manager│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌───────────────────────────────┐                          │
│  │ Trigger Runner                │                          │
│  │ (Webhook, Schedule, Events)   │                          │
│  └───────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Agent Runtime│  │ Memory System│  │ Tool Registry    │   │
│  └──────────────┘  └──────────────┘  │ + Tool Executor  │   │
│                                      └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   COMMUNICATION LAYER                       │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ Message Bus  │  │ Event Stream     │  │ Pub/Sub      │   │
│  └──────────────┘  │ + Event Router   │  └──────────────┘   │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ LLM Providers│  │ Vector DBs   │  │ Observability│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────────────┐  ┌───────────────────────────┐    │
│  │ Persistent Stores    │  │ Connectors / Integrations │    │
│  │ (Postgres, Redis,…)  │  │ (Slack, Kafka, Jira, …)   │    │
│  └──────────────────────┘  └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│      CROSS-CUTTING (ALL LAYERS): SECURITY / GOVERNANCE      │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ RBAC         │  │ Policy Engine    │  │ Audit Logging│   │
│  │              │  │ (ACL + approvals)│  │              │   │
│  └──────────────┘  └──────────────────┘  └──────────────┘   │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │ Guardrails       │  │ Secrets + Encryption (configs) │   │
│  │ (PII, filters, …)│  │                                │   │
│  └──────────────────┘  └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```


See [ARCHITECTURE.md](./ARCHITECTURE.md) for complete details.

---

## 💡 Quick Start

### CLI Quick Start (OSS)

The OSS package ships a `genxai` CLI with `tool` and `workflow` commands.

```bash
# Verify the CLI entry point
genxai --help

# List available tools
genxai tool list

# Search and inspect tools
genxai tool search weather
genxai tool info weather_api

# Run a YAML workflow
genxai workflow run examples/nocode/content_generation.yaml \
  --input '{"topic": "AI workflow design"}'

# Create and export a tool
genxai tool create \
  --name my_tool \
  --description "My custom tool" \
  --category custom \
  --template api_call \
  --config '{"url": "https://api.example.com", "method": "GET"}'
genxai tool export my_tool --output ./my_tool.json

# Import a tool and export schema bundles
genxai tool import-tool ./my_tool.json
genxai tool export-schema --output tool_schemas.json
genxai tool export-schema --format yaml --output tool_schemas.yaml
```

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

### Trigger SDK Quick Start (OSS)

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

# Full install with providers/tools/API (core)
pip install "genxai-framework[llm,tools,api]"

# Everything included
pip install "genxai-framework[all]"
```

> The Studio UI is planned for a separate commercial repository and is not included here.

---

## 🧩 OSS Enterprise Features (Studio Excluded)

The following enterprise-grade capabilities are **included in OSS**:

- **Connectors**: Kafka, SQS, Postgres CDC, Webhooks, Slack, GitHub, Notion, Jira, Google Workspace
- **Triggers**: Webhook, schedule, and queue triggers
- **Observability**: logging, metrics, tracing, alerts
- **Security**: RBAC, policy engine, audit logging, rate limits, PII utilities
- **CLI Extensions**: metrics, connector, approval, audit commands
- **Worker Queue Engine**: distributed execution support

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

## 👥 Contributors

| Name | Email |
| --- | --- |
| Irsal Imran | [irsal2025@gmail.com](mailto:irsal2025@gmail.com) |

---

## 📜 License

MIT License

---

## 🔗 Links

- **Documentation**: See docs/ directory
- **GitHub**: https://github.com/genexsus-ai/genxai
- **Discord**: (To be created)
- **Website**: https://www.genxai.dev

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
