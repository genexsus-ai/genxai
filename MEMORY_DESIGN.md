# GenXAI Framework - Memory System Design

**Version:** 1.0.0  
**Last Updated:** February 3, 2026  
**Status:** Active Development

---

## Overview

GenXAI provides a multi-layered memory system modeled after human cognition.
It is designed to support both short-lived context and persistent knowledge
across agents and workflows.

### Memory Layers

1. **Short-Term Memory** – recent conversational context (token-limited)
2. **Working Memory** – temporary scratch space during execution
3. **Long-Term Memory** – persistent, searchable knowledge store
4. **Episodic Memory** – event-based experiences with metadata
5. **Semantic Memory** – factual knowledge with relationships
6. **Procedural Memory** – step-based procedures and learned skills

---

## Architecture

```text
Agent Runtime
  ├─ Short-Term Memory (token window)
  ├─ Working Memory (scratchpad)
  ├─ Episodic / Semantic / Procedural Stores
  └─ Long-Term Store (persistent backend)
```

Each layer can be enabled or disabled per agent. A workflow can also provide a
**shared memory** layer that is injected into all agents during execution.

---

## Core Interfaces

```python
from pathlib import Path
from genxai.core.memory.manager import MemorySystem

memory = MemorySystem(
    agent_id="assistant",
    persistence_enabled=True,
    persistence_path=Path(".genxai/memory"),
)
```

### Key Operations

- `add_to_short_term(content, metadata=None)`
- `get_short_term_context(max_tokens=4000)`
- `add_to_long_term(memory, ttl=None)`
- `search_long_term(query, limit=10)`
- `store_episode(task, actions, outcome, duration, success, metadata=None)`
- `store_fact(subject, predicate, object, confidence=1.0, source=None)`
- `store_procedure(name, description, steps, preconditions=None, postconditions=None)`
- `get_stats()`

---

## Configuration

### Agent-Level Memory

```python
agent = AgentFactory.create_agent(
    id="assistant",
    role="Assistant",
    goal="Help the user",
    enable_memory=True,
)
```

### Workflow-Level Shared Memory (YAML)

```yaml
workflow:
  name: "Shared Memory Example"
  memory:
    shared: true
    type: "short_term"
  agents:
    - id: "agent_one"
      role: "Agent One"
      memory:
        enabled: false
```

---

## Persistence

Persistence can be enabled per agent or per workflow. When enabled, the memory
system writes snapshots to disk (or a configured backend) and loads them on
startup.

```python
memory = MemorySystem(
    agent_id="assistant",
    persistence_enabled=True,
    persistence_path=Path(".genxai/memory"),
)
```

### Storage Backends

- **Local FS** (default): `.genxai/memory/`
- **Vector DB**: planned via adapters (Pinecone, Weaviate, Chroma)
- **Graph DB**: planned for semantic/episodic relationships

---

## Memory Types (Details)

### Short-Term Memory
- Token-limited context window
- Optimized for LLM prompt construction

### Working Memory
- Scratchpad for intermediate computation
- Cleared between runs unless persisted manually

### Long-Term Memory
- Persistent knowledge storage
- Semantic search supported

### Episodic Memory
- Stores events and execution outcomes
- Useful for learning and regression analysis

### Semantic Memory
- Stores facts and relationships
- Optimized for queryable knowledge graphs

### Procedural Memory
- Stores multi-step procedures and skills
- Enables reusable playbooks

---

## Best Practices

1. **Keep short-term memory small** to avoid prompt bloat.
2. **Use shared memory** when agents need consistent context.
3. **Persist only high-value information** to limit storage costs.
4. **Use semantic memory** for facts, episodic memory for interactions.

---

## Known Limitations

- Long-term storage adapters are still evolving.
- Semantic and procedural persistence is limited to configured backends.
- Large shared memory payloads can slow down agent prompts.

---

## Roadmap

- Vector-backed long-term memory adapters
- Episodic/semantic graph store integration
- Memory consolidation utilities
- Memory usage metrics and dashboards

---

## Status

This document captures the intended design and the currently implemented
interfaces. As the memory system evolves, this document will be updated to
reflect new storage backends and optimization strategies.
