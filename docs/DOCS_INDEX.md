# GenXAI Documentation Index

Complete guide to GenXAI framework documentation.

---

## 🚀 Getting Started

| Document | Description |
|----------|-------------|
| [README](../README.md) | Project overview and quick start |
| [GETTING_STARTED](../GETTING_STARTED.md) | Installation and first workflow |
| [QUICK_START_TUTORIAL](./QUICK_START_TUTORIAL.md) | Step-by-step tutorial with examples |

---

## 📚 Core Concepts

| Document | Description |
|----------|-------------|
| [ARCHITECTURE](../ARCHITECTURE.md) | System architecture and design principles |
| [WORKFLOW_BEST_PRACTICES](./WORKFLOW_BEST_PRACTICES.md) | Best practices for workflow design |
| [AGENT_CATALOG](./AGENT_CATALOG.md) | Every reusable agent and agent-team primitive, with application recipes |
| [AGENT_TOOL_INTEGRATION](./AGENT_TOOL_INTEGRATION.md) | Agent and tool integration guide |
| [FLOWS](./FLOWS.md) | Flow orchestrators for common coordination patterns |
| [WORKFLOW_GENERATION](./WORKFLOW_GENERATION.md) | Natural-language workflow generation with the planner/delegator/worker crew |
| [WORKFLOW_COMPOSITION](./WORKFLOW_COMPOSITION.md) | Compose global workflows with subflows + deterministic steps |
| [WORKFLOW_COMPOSITION_JSON](./diagrams/workflow_composition.json) | JSON snapshot of the workflow composition graph |
| [COMPARISON](./COMPARISON.md) | CrewAI vs GenXAI comparison guide |

---

## 🔧 API & SDK Reference

| Document | Description |
|----------|-------------|
| [API_REFERENCE](./API_REFERENCE.md) | Complete API reference with examples |
| [API](./API.md) | Condensed API guide |
| [CONNECTOR_SDK (OSS Runtime)](./CONNECTOR_SDK.md) | Connector SDK for external integrations |
| [LLM_INTEGRATION](./LLM_INTEGRATION.md) | LLM provider integration guide |

---

## 🛠️ Tools & CLI

| Document | Description |
|----------|-------------|
| [CLI_USAGE (OSS Runtime)](./CLI_USAGE.md) | OSS CLI (`genxai tool/workflow/connector/metrics/approval/audit`) |
| [TOOL_CREATION](./TOOL_CREATION.md) | Creating custom tools |
| [MCP_SETUP](./MCP_SETUP.md) | Model Context Protocol server setup |

---

## 🔐 Security & Governance

| Document | Description |
|----------|-------------|
| [GOVERNANCE_POLICY (OSS Runtime)](./GOVERNANCE_POLICY.md) | Policy engine and ACL configuration |
| [AUDIT_LOGGING (OSS Runtime)](./AUDIT_LOGGING.md) | Audit logging and compliance |
| [SECURITY_CHECKLIST (OSS Runtime)](./SECURITY_CHECKLIST.md) | Pre-release security checklist |

---

## 🚢 Deployment & Operations

| Document | Description |
|----------|-------------|
| [WORKER_QUEUE_ENGINE (OSS Runtime)](./WORKER_QUEUE_ENGINE.md) | Worker queue and task distribution |
| [HARD_ISOLATION_GUIDE (OSS Runtime)](./HARD_ISOLATION_GUIDE.md) | Process/container isolation strategy for agents |
| [BENCHMARKING](./BENCHMARKING.md) | Performance benchmarking guide |
| [GRAPH_VISUALIZATION](./GRAPH_VISUALIZATION.md) | Workflow graph visualization |

---

## 📦 Release & Publishing

| Document | Description |
|----------|-------------|
| [RELEASE_CHECKLIST](./RELEASE_CHECKLIST.md) | Pre-release checklist |
| [PUBLISHING](./PUBLISHING.md) | PyPI publishing guide |

---

## 🏢 Roadmap

| Document | Description |
|----------|-------------|
| [COMPETITIVE_MATRIX](./COMPETITIVE_MATRIX.md) | Comparison vs CrewAI, AutoGen, BeeAI, LangChain |

---

## 🧩 Production-Grade Features

The runtime includes production-grade capabilities:

- **Connectors**: Kafka, SQS, Postgres CDC, Webhooks, Slack, GitHub, Notion, Jira, Google Workspace
- **Triggers**: Webhook, schedule, queue triggers
- **Observability**: logging, metrics, tracing, alerts
- **Security**: RBAC, policy engine, audit logging, rate limits, PII utilities
- **CLI Extensions**: metrics, connector, approval, audit commands
- **Worker Queue Engine**: distributed execution

---

## 🤝 Contributing

| Document | Description |
|----------|-------------|
| [CONTRIBUTING](../CONTRIBUTING.md) | Contribution guidelines |

---

## 📖 Additional Resources

### Collaboration & Communication
- [COLLABORATION_PROTOCOLS](./COLLABORATION_PROTOCOLS.md) - Agent collaboration patterns

### Examples
- [examples/code/](../examples/code/) - Code-based workflow examples
  - Flow examples: `flow_parallel_example.py`, `flow_conditional_example.py`,
    `flow_loop_example.py`, `flow_router_example.py`, `flow_ensemble_voting_example.py`,
    `flow_critic_review_example.py`, `flow_coordinator_worker_example.py`,
    `flow_map_reduce_example.py`, `flow_subworkflow_example.py`, `flow_auction_example.py`
- [examples/nocode/](../examples/nocode/) - YAML workflow templates
- [examples/patterns/](../examples/patterns/) - Common workflow patterns

### Studio (Visual Workflow Builder)
- A no-code drag-and-drop workflow builder (Workflow Studio) lives in this repo at `applications/workflow_studio/` (its own git repository, excluded from the package build). See its README for setup.

---

## 🔍 Quick Reference

### By Use Case

**Building Your First Workflow**
1. [GETTING_STARTED](../GETTING_STARTED.md)
2. [QUICK_START_TUTORIAL](./QUICK_START_TUTORIAL.md)
3. [WORKFLOW_BEST_PRACTICES](./WORKFLOW_BEST_PRACTICES.md)

**Integrating External Systems**
1. [CONNECTOR_SDK (OSS Runtime)](./CONNECTOR_SDK.md)
2. [API_REFERENCE](./API_REFERENCE.md) (OSS Triggers & Connectors section)
3. [LLM_INTEGRATION](./LLM_INTEGRATION.md)

**Production Deployment**
1. [WORKER_QUEUE_ENGINE (OSS Runtime)](./WORKER_QUEUE_ENGINE.md)
2. [GOVERNANCE_POLICY (OSS Runtime)](./GOVERNANCE_POLICY.md)
3. [AUDIT_LOGGING (OSS Runtime)](./AUDIT_LOGGING.md)
4. [SECURITY_CHECKLIST (OSS Runtime)](./SECURITY_CHECKLIST.md)

**CLI & Automation**
1. [CLI_USAGE (OSS Runtime)](./CLI_USAGE.md)
2. [MCP_SETUP](./MCP_SETUP.md)

**Performance & Monitoring**
1. [BENCHMARKING](./BENCHMARKING.md)
2. [GRAPH_VISUALIZATION](./GRAPH_VISUALIZATION.md)

---

## 📝 Document Status

| Status | Meaning |
|--------|---------|
| ✅ Complete | Fully documented and up-to-date |
| 🔄 In Progress | Actively being updated |
| 📋 Planned | Scheduled for future updates |

### Current Status

- ✅ API_REFERENCE.md
- ✅ QUICK_START_TUTORIAL.md
- ✅ AGENT_TOOL_INTEGRATION.md
- ✅ COMPETITIVE_MATRIX.md
- ✅ CLI_USAGE.md
- ✅ BENCHMARKING.md
- ✅ GOVERNANCE_POLICY.md
- ✅ RELEASE_CHECKLIST.md
- ✅ SECURITY_CHECKLIST.md
- ✅ CONNECTOR_SDK.md
- ✅ WORKER_QUEUE_ENGINE.md
- ✅ AUDIT_LOGGING.md
- ✅ COLLABORATION_PROTOCOLS.md

---

## 🆘 Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/genexsus-ai/genxai-framework/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/genexsus-ai/genxai-framework/discussions)
- **Documentation**: Start with [GETTING_STARTED](../GETTING_STARTED.md)

---

**Last Updated**: July 2026
