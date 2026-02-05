# GenXAI Workflow Patterns

This directory contains comprehensive examples of workflow patterns that can be implemented using the GenXAI framework. Each pattern demonstrates a different orchestration strategy for multi-agent systems.

## 📋 Available Patterns

### 1. Sequential Pattern
**File:** `01_sequential_pattern.py`

Linear agent chain where each agent processes output from the previous agent.

```
Input → Agent1 → Agent2 → Agent3 → Output
```

**Use Cases:**
- Document processing pipelines
- Data transformation chains
- Step-by-step analysis workflows
- ETL (Extract-Transform-Load) processes

**Key Features:**
- Simple and predictable
- Clear data lineage
- Easy to debug

---

### 2. Conditional Branching Pattern
**File:** `02_conditional_branching.py`

Decision-based routing where workflow branches based on runtime conditions.

```
                ┌─→ Agent A
Input → Router ─┼─→ Agent B
                └─→ Agent C
```

**Use Cases:**
- Customer support ticket routing
- Content categorization
- Risk-based processing
- Multi-tier service levels

**Key Features:**
- Flexible routing logic
- Specialized agents per scenario
- Efficient resource utilization

---

### 3. Parallel Execution Pattern
**File:** `03_parallel_execution.py`

Multiple agents process the same input concurrently, results are aggregated.

```
              ┌─→ Agent1 ─┐
Input → Split ┼─→ Agent2 ─┼→ Aggregate → Output
              └─→ Agent3 ─┘
```

**Use Cases:**
- Multi-perspective analysis
- Parallel data processing
- Consensus building
- Competitive evaluation

**Key Features:**
- Significant time savings
- Multiple perspectives
- Fault tolerance

---

### 4. Coordinator-Delegator-Worker (CDW) Pattern
**File:** `04_coordinator_delegator_worker.py`

Hierarchical pattern with coordinator oversight, task delegation, and specialized workers.

```
    Coordinator
         ↓
    Delegator
    ↓    ↓    ↓
Worker1 Worker2 Worker3
    ↓    ↓    ↓
    Aggregator
```

**Use Cases:**
- Complex project management
- Distributed task processing
- Multi-specialist collaboration
- Large-scale data processing

**Key Features:**
- Clear separation of responsibilities
- Scalable worker pool
- Quality oversight
- Parallel execution

---

### 5. Cyclic/Iterative Pattern
**File:** `05_cyclic_iterative.py`

Feedback loop where outputs are validated and refined iteratively.

```
Generator → Validator → (if pass) → Finalizer
                ↓
            (if fail)
                ↓
            Refiner ──┘
```

**Use Cases:**
- Iterative content refinement
- Quality assurance loops
- Self-correction workflows
- Continuous improvement

**Key Features:**
- Continuous quality improvement
- Self-correcting
- Flexible iteration count
- Learns from feedback

---

### 6. Peer-to-Peer (P2P) Pattern
**File:** `06_peer_to_peer.py`

Decentralized agent communication where agents interact directly without a central manager.

```
Agent1 ←→ Agent2
  ↕         ↕
Agent3 ←→ Agent4
```

**Use Cases:**
- Collaborative problem-solving
- Distributed decision-making
- Multi-agent negotiation
- Consensus building
- Peer review systems

**Key Features:**
- No central coordinator
- Direct agent-to-agent communication
- Multiple termination strategies
- Emergent behavior
- Consensus-based decisions

---

## 🚀 Running the Examples

### Prerequisites

```bash
# Install GenXAI framework
pip install -e .

# Set OpenAI API key (optional for simulation)
export OPENAI_API_KEY='your-key-here'
```

### Run Individual Patterns

```bash
# Sequential pattern
python examples/patterns/01_sequential_pattern.py

# Conditional branching
python examples/patterns/02_conditional_branching.py

# Parallel execution
python examples/patterns/03_parallel_execution.py

# CDW pattern
python examples/patterns/04_coordinator_delegator_worker.py

# Cyclic/iterative
python examples/patterns/05_cyclic_iterative.py

# Peer-to-peer
python examples/patterns/06_peer_to_peer.py
```

### Run All Patterns

```bash
# Run all pattern examples
for file in examples/patterns/0*.py; do
    echo "Running $file..."
    python "$file"
    echo "---"
done
```

## 📊 Pattern Comparison

| Pattern | Complexity | Speed | Scalability | Use Case |
|---------|-----------|-------|-------------|----------|
| Sequential | Low | Slow | Low | Simple pipelines |
| Conditional | Medium | Medium | Medium | Routing/classification |
| Parallel | Medium | Fast | High | Independent tasks |
| CDW | High | Fast | Very High | Complex projects |
| Cyclic | Medium | Slow | Medium | Quality refinement |
| P2P | Medium-High | Medium | High | Collaborative/Distributed |

## 🎯 Choosing the Right Pattern

### Use **Sequential** when:
- Tasks must be done in order
- Each step depends on previous output
- Simplicity is priority

### Use **Conditional Branching** when:
- Different scenarios need different handling
- You have specialized agents
- Routing logic is clear

### Use **Parallel Execution** when:
- Tasks are independent
- Speed is critical
- Multiple perspectives needed

### Use **CDW** when:
- Complex multi-step projects
- Need quality oversight
- Multiple specializations required
- Scalability is important

### Use **Cyclic/Iterative** when:
- Quality standards are high
- Refinement is expected
- Feedback improves output

### Use **P2P** when:
- Agents need to collaborate as equals
- No clear hierarchy exists
- Consensus-based decisions required
- Distributed problem-solving needed
- Emergent solutions are acceptable

## 🔧 Customization

Each pattern can be customized by:

1. **Changing Agents**: Modify roles, goals, and tools
2. **Adjusting Conditions**: Update routing logic
3. **Adding Nodes**: Extend with more agents
4. **Modifying Edges**: Change flow connections
5. **Tuning Parameters**: Adjust temperature, thresholds

### Example: Adding an Agent

```python
# Add a new agent
new_agent = AgentFactory.create_agent(
    id="new_agent",
    role="New Role",
    goal="Specific goal",
    tools=["tool1", "tool2"]
)

# Add to graph
graph.add_node(AgentNode(id="new_node", agent_id="new_agent"))
graph.add_edge(Edge(source="previous_node", target="new_node"))
```

## 📚 Advanced Patterns

Coming soon:
- Map-Reduce Pattern
- Saga Pattern (long-running transactions)
- Human-in-the-Loop Pattern
- Hierarchical CDW (multi-level)
- Dynamic Worker Pool
- Competitive Workers

## 🐛 Debugging Tips

1. **Enable Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Validate Graph**:
```python
graph.validate()  # Check for errors
```

3. **Visualize Workflow**:
```python
graph.visualize()  # See graph structure
```

4. **Track State**:
```python
# Monitor state changes
print(state_manager.to_dict())
```

## 📖 Additional Resources

- [GenXAI Documentation](../../README.md)
- [Architecture Guide](../../ARCHITECTURE.md)
- [Best Practices](../../docs/WORKFLOW_BEST_PRACTICES.md)
- [API Reference](../../docs/API.md)

## 🤝 Contributing

Have a new pattern to share? Contributions welcome!

1. Create pattern file: `0X_pattern_name.py`
2. Follow existing format
3. Add documentation
4. Submit pull request

## 📝 License

MIT License - see [LICENSE](../../LICENSE) for details

---

**Built with ❤️ using GenXAI Framework**
