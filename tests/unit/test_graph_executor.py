"""Tests for graph executor."""

import pytest
from genxai.core.graph.executor import WorkflowExecutor, EnhancedGraph, execute_workflow_sync
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.tools.registry import ToolRegistry
from genxai.core.graph.engine import GraphExecutionError, Graph
from genxai.core.graph.nodes import ToolNode


def test_workflow_executor_initialization():
    """Test workflow executor initialization."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    assert executor is not None
    assert executor.openai_api_key is None


def test_workflow_executor_with_api_key():
    """Test workflow executor with API key."""
    executor = WorkflowExecutor(
        openai_api_key="test_key",
        register_builtin_tools=False
    )
    assert executor.openai_api_key == "test_key"


def test_workflow_executor_registers_tools():
    """Test that executor registers built-in tools."""
    # Clear registry first
    ToolRegistry.clear()
    
    # Create executor with tool registration
    executor = WorkflowExecutor(register_builtin_tools=True)
    
    # Verify tools were registered
    stats = ToolRegistry.get_stats()
    assert stats["total_tools"] >= 2  # At least calculator and file_reader


def test_create_agents_from_nodes():
    """Test creating agents from node definitions."""
    AgentRegistry.clear()
    
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    nodes = [
        {
            "id": "agent1",
            "type": "agent",
            "config": {
                "role": "Test Agent",
                "goal": "Test goal",
                "llm_model": "gpt-4"
            }
        }
    ]
    
    executor._create_agents_from_nodes(nodes)
    
    # Verify agent was created and registered
    agent = AgentRegistry.get("agent1")
    assert agent is not None
    assert agent.config.role == "Test Agent"
    
    AgentRegistry.clear()


def test_build_graph_with_input_output():
    """Test building graph with input and output nodes."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    nodes = [
        {"id": "input", "type": "input"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {"source": "input", "target": "output"}
    ]
    
    graph = executor._build_graph(nodes, edges)
    
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert "input" in graph.nodes
    assert "output" in graph.nodes


def test_build_graph_with_agent_node():
    """Test building graph with agent node."""
    AgentRegistry.clear()
    
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    # Create agent first
    agent = AgentFactory.create_agent(
        id="test_agent",
        role="Test",
        goal="Test",
        llm_model="gpt-4"
    )
    AgentRegistry.register(agent)
    
    nodes = [
        {"id": "input", "type": "input"},
        {"id": "test_agent", "type": "agent"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {"source": "input", "target": "test_agent"},
        {"source": "test_agent", "target": "output"}
    ]
    
    graph = executor._build_graph(nodes, edges)
    
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    
    AgentRegistry.clear()


def test_build_graph_with_conditional_edge():
    """Test building graph with conditional edge."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    nodes = [
        {"id": "input", "type": "input"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {
            "source": "input",
            "target": "output",
            "condition": "some_condition"
        }
    ]
    
    graph = executor._build_graph(nodes, edges)
    
    assert len(graph.edges) == 1


def test_evaluate_condition_true():
    """Test evaluating a true condition."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    state = {"some_key": "value"}
    result = executor._evaluate_condition(state, "some_key")
    
    assert result is True


def test_evaluate_condition_false():
    """Test evaluating a false condition."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    state = {"some_key": "value"}
    result = executor._evaluate_condition(state, "missing_key")
    
    assert result is False


@pytest.mark.asyncio
async def test_execute_simple_workflow():
    """Test executing a simple workflow."""
    AgentRegistry.clear()
    
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    nodes = [
        {"id": "input", "type": "input"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {"source": "input", "target": "output"}
    ]
    
    input_data = {"message": "test"}
    
    result = await executor.execute(nodes, edges, input_data)
    
    assert result["status"] == "success"
    assert "result" in result
    
    AgentRegistry.clear()


@pytest.mark.asyncio
async def test_execute_workflow_with_error():
    """Test executing workflow with invalid configuration."""
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    # Invalid nodes (missing required fields)
    nodes = []
    edges = []
    
    result = await executor.execute(nodes, edges, {})
    
    assert result["status"] == "error"
    assert "error" in result


def test_enhanced_graph_initialization():
    """Test enhanced graph initialization."""
    graph = EnhancedGraph(name="test_graph")
    assert graph.name == "test_graph"
    assert len(graph.nodes) == 0


@pytest.mark.asyncio
async def test_enhanced_graph_execute_input_node():
    """Test enhanced graph executing input node."""
    graph = EnhancedGraph(name="test")
    
    input_node = InputNode()
    graph.add_node(input_node)
    
    state = {"input": {"data": "test"}}
    result = await graph._execute_node_logic(input_node, state)
    
    assert result == {"data": "test"}


@pytest.mark.asyncio
async def test_enhanced_graph_execute_output_node():
    """Test enhanced graph executing output node."""
    graph = EnhancedGraph(name="test")
    
    output_node = OutputNode()
    graph.add_node(output_node)
    
    state = {"key": "value"}
    result = await graph._execute_node_logic(output_node, state)
    
    assert "key" in result
    assert result["key"] == "value"


def test_execute_workflow_sync_wrapper():
    """Test synchronous workflow execution wrapper."""
    nodes = [
        {"id": "input", "type": "input"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {"source": "input", "target": "output"}
    ]
    
    input_data = {"test": "data"}
    
    result = execute_workflow_sync(nodes, edges, input_data)
    
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_workflow_executor_cleanup():
    """Test that executor cleans up registries."""
    AgentRegistry.clear()
    
    executor = WorkflowExecutor(register_builtin_tools=False)
    
    # Create agent
    nodes = [
        {
            "id": "agent1",
            "type": "agent",
            "config": {"role": "Test", "goal": "Test"}
        },
        {"id": "input", "type": "input"},
        {"id": "output", "type": "output"}
    ]
    
    edges = [
        {"source": "input", "target": "output"}
    ]
    
    # Execute workflow
    await executor.execute(nodes, edges, {})
    
    # Verify registry was cleared
    assert len(AgentRegistry.list_all()) == 0


@pytest.mark.asyncio
async def test_graph_run_with_no_entry_point():
    """Graph should error when no entry point exists."""
    graph = Graph(name="empty")

    with pytest.raises(GraphExecutionError):
        await graph.run(input_data={})


@pytest.mark.asyncio
async def test_graph_max_iterations_exceeded():
    """Graph should raise when max iterations exceeded."""
    graph = Graph(name="loop")
    graph.add_node(InputNode(id="start"))
    graph.add_node(OutputNode(id="end"))
    graph.add_edge(Edge(source="start", target="end"))
    graph.add_edge(Edge(source="end", target="start"))

    with pytest.raises(GraphExecutionError):
        await graph.run(input_data={}, max_iterations=1)


@pytest.mark.asyncio
async def test_tool_node_missing_tool_name():
    """Tool node without tool_name should raise GraphExecutionError."""
    graph = Graph(name="tool-missing")
    tool_node = ToolNode(id="tool", tool_name=None)
    graph.add_node(tool_node)

    with pytest.raises(GraphExecutionError):
        await graph._execute_tool_node(tool_node, {})


@pytest.mark.asyncio
async def test_tool_node_missing_tool_in_registry():
    """Tool node should error when tool is not in registry."""
    graph = Graph(name="tool-missing-registry")
    tool_node = ToolNode(id="tool", tool_name="calculator")
    graph.add_node(tool_node)
    ToolRegistry.clear()

    with pytest.raises(GraphExecutionError):
        await graph._execute_tool_node(tool_node, {})
