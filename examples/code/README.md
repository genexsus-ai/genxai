# GenXAI Code Examples

This directory contains runnable code examples demonstrating GenXAI framework features.

## Examples

### 1. `testable_workflow.py` - **Fully Testable Workflow** ⭐ RECOMMENDED

A complete, runnable workflow example that demonstrates:
- ✅ Real agent instances with AgentRegistry
- ✅ Actual tool execution (calculator, file_reader)
- ✅ Proper graph execution with agent integration
- ✅ Works with or without API key (graceful degradation)

**Run it:**
```bash
python examples/code/testable_workflow.py
```

**What it tests:**
- **Scenario 1**: Calculator workflow (no API key needed)
- **Scenario 2**: File processing workflow (no API key needed)
- **Scenario 3**: Multi-agent sequential workflow

**Output:**
```
╔════════════════════════════════════════════════════════════════════╗
║               GenXAI - Fully Testable Workflow                     ║
╚════════════════════════════════════════════════════════════════════╝

ℹ️  Note: OPENAI_API_KEY not set
   Workflows will run with simulated agent responses
   Tools (calculator, file_reader) will execute normally

======================================================================
SCENARIO 1: Calculator Workflow
======================================================================
...
```

### 2. `simple_workflow.py` - Basic Graph Structure

Demonstrates basic graph construction with nodes and edges.

**Note:** This example shows structure but doesn't execute fully (agents not registered).

### 3. `end_to_end_example.py` - Comprehensive Demo

Shows all GenXAI features with detailed explanations.

**Note:** This example is educational but uses simulated execution.

### 4. `llm_agent_example.py` - LLM Agent Variations

Demonstrates:
- Basic agent execution with real LLMs
- Personality/backstory
- Deliberative agent behavior
- Batch execution

### 5. `agent_with_tools_example.py` - Tool-Enabled Agent

Shows how to register and attach tools to a runtime.

### 6. `agent_registry_example.py` - Agent Registry Basics

Register agents globally and retrieve them by ID.

### 7. `memory_system_example.py` - Memory System Overview

Exercises short-term, long-term, semantic, and procedural memories.

### 8. `tool_registry_example.py` - Tool Registry Stats

Lists built-in tools and prints a tool schema.

### 9. `tool_execution_example.py` - Run a Built-in Tool

Executes the calculator tool without an LLM.

### 10. `graph_visualization_example.py` - Workflow Visualization

Generates ASCII, Mermaid, and DOT outputs from a graph.

### 11. `workflow_engine_example.py` - WorkflowEngine Wrapper

Demonstrates the compatibility `WorkflowEngine` execute call.

### 12. `routed_llm_provider_example.py` - Routed LLM Provider

Shows a primary model with fallback providers.

### 13. `agent_with_memory_tools_example.py` - Tools + Memory Runtime

Combines tool execution and memory context in a single agent.

### 14. `function_calling_tools_example.py` - Schema-Based Tool Calling

Uses OpenAI function calling to select tools via schemas.

### 15. `simple_workflow.py` - Intro Workflow

Basic graph setup example.

### 16. `end_to_end_example.py` - Full Walkthrough

Comprehensive end-to-end flow.

## Key Differences

| Feature | testable_workflow.py | simple_workflow.py | end_to_end_example.py |
|---------|---------------------|-------------------|----------------------|
| **Fully Runnable** | ✅ Yes | ❌ No | ⚠️ Simulated |
| **Agent Registry** | ✅ Yes | ❌ No | ❌ No |
| **Tool Execution** | ✅ Real | ❌ No | ✅ Real |
| **Graph Execution** | ✅ Complete | ⚠️ Partial | ⚠️ Simulated |
| **No API Key Needed** | ✅ Yes | ✅ Yes | ✅ Yes |

## Architecture

### Agent Registry System

The `testable_workflow.py` example introduces `AgentRegistry` to properly manage agent instances:

```python
from genxai.core.agent.registry import AgentRegistry

# Create agent
agent = AgentFactory.create_agent(
    id="math_agent",
    role="Mathematics Expert",
    tools=["calculator"]
)

# Register agent
AgentRegistry.register(agent)

# Use in graph
graph.add_node(AgentNode(id="math_node", agent_id="math_agent"))
```

### Enhanced Graph Execution

The `EnhancedGraph` class extends the base `Graph` to:
1. Retrieve agents from registry
2. Execute agents with tool support
3. Integrate tool results into agent output

```python
class EnhancedGraph(Graph):
    async def _execute_node_logic(self, node, state):
        if node.type == NodeType.AGENT:
            agent = AgentRegistry.get(node.config.agent_id)
            result = await self._execute_agent_with_tools(agent, task, state)
            return result
```

## Running Examples

### Prerequisites

```bash
# Install GenXAI
pip install -e .

# Optional: Set API key for full LLM integration
export OPENAI_API_KEY='your-api-key'
```

### Run Testable Workflow

```bash
# From project root
python examples/code/testable_workflow.py
```

### Expected Output

The workflow will:
1. ✅ Register tools (calculator, file_reader)
2. ✅ Create and register agents
3. ✅ Build graph workflows
4. ✅ Execute workflows with real tool execution
5. ✅ Display results and statistics

## Next Steps

After running the testable workflow:

1. **Modify scenarios** - Edit `testable_workflow.py` to test your own workflows
2. **Add custom tools** - Create tools in `genxai/tools/custom/`
3. **Create custom agents** - Define agents with specific roles and tools
4. **Build complex graphs** - Add conditional routing, parallel execution, etc.

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Make sure you're in the project root
cd /path/to/GenXAI

# Install in development mode
pip install -e .
```

### Tool Not Found

If tools aren't found:
```python
# Check registered tools
from genxai.tools.registry import ToolRegistry
print(ToolRegistry.list_all())
```

### Agent Not Found

If agents aren't found:
```python
# Check registered agents
from genxai.core.agent.registry import AgentRegistry
print(AgentRegistry.list_all())
```

## Contributing

To add new examples:
1. Create a new `.py` file in this directory
2. Follow the pattern in `testable_workflow.py`
3. Include clear documentation and comments
4. Update this README with your example

## Support

For issues or questions:
- GitHub Issues: https://github.com/irsal2012/GenXAI/issues
- Documentation: See `/docs` folder
