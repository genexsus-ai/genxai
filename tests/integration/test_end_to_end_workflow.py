"""End-to-end workflow integration tests."""

import pytest
import os
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *


@pytest.mark.integration
def test_graph_creation_and_validation():
    """Test creating and validating a graph."""
    graph = Graph(name="test_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="agent1", agent_id="test_agent"))
    graph.add_node(OutputNode())
    
    # Add edges
    graph.add_edge(Edge(source="input", target="agent1"))
    graph.add_edge(Edge(source="agent1", target="output"))
    
    # Validate
    assert graph.validate() is True
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_simple_workflow_execution():
    """Test executing a simple workflow."""
    graph = Graph(name="simple_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(OutputNode())
    
    # Add edge
    graph.add_edge(Edge(source="input", target="output"))
    
    # Run workflow
    result = await graph.run(input_data={"message": "test"})
    
    assert result is not None
    assert "input" in result


@pytest.mark.integration
def test_agent_with_tools_setup():
    """Test setting up an agent with tools."""
    # Create agent
    agent = AgentFactory.create_agent(
        id="tool_agent",
        role="Tool User",
        goal="Use tools effectively",
        tools=["calculator"],
        llm_model="gpt-4",
    )
    
    # Get tool from registry
    calculator = ToolRegistry.get("calculator")
    assert calculator is not None
    
    # Create runtime
    runtime = AgentRuntime(agent=agent)
    runtime.set_tools({"calculator": calculator})
    
    assert runtime._tools is not None
    assert "calculator" in runtime._tools


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_execution():
    """Test executing a tool."""
    from genxai.tools.builtin.computation.calculator import CalculatorTool
    
    calculator = CalculatorTool()
    result = await calculator.execute(expression="2 + 2")
    
    assert result.success is True
    assert result.data["result"] == 4.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_agent_graph_structure():
    """Test creating a multi-agent graph structure."""
    graph = Graph(name="multi_agent")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="agent1", agent_id="researcher"))
    graph.add_node(AgentNode(id="agent2", agent_id="writer"))
    graph.add_node(OutputNode())
    
    # Add edges (sequential)
    graph.add_edge(Edge(source="input", target="agent1"))
    graph.add_edge(Edge(source="agent1", target="agent2"))
    graph.add_edge(Edge(source="agent2", target="output"))
    
    # Validate
    assert graph.validate() is True
    assert len(graph.nodes) == 4
    assert len(graph.edges) == 3


@pytest.mark.integration
def test_graph_visualization():
    """Test graph visualization methods."""
    graph = Graph(name="viz_test")
    
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="agent1", agent_id="test"))
    graph.add_node(OutputNode())
    
    graph.add_edge(Edge(source="input", target="agent1"))
    graph.add_edge(Edge(source="agent1", target="output"))
    
    # Test ASCII visualization
    ascii_viz = graph.draw_ascii()
    assert "viz_test" in ascii_viz
    assert "input" in ascii_viz
    
    # Test Mermaid format
    mermaid = graph.to_mermaid()
    assert "graph TD" in mermaid
    
    # Test DOT format
    dot = graph.to_dot()
    assert "digraph" in dot


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_system_integration():
    """Test memory system integration."""
    from genxai.core.memory.manager import MemorySystem
    
    memory = MemorySystem(agent_id="test_agent")
    
    # Add to short-term
    await memory.add_to_short_term(
        content={"message": "Test message"},
        metadata={"timestamp": 123456}
    )
    
    # Get context
    context = await memory.get_short_term_context(max_tokens=1000)
    assert context is not None
    
    # Get stats
    stats = await memory.get_stats()
    assert "agent_id" in stats
    assert stats["agent_id"] == "test_agent"


@pytest.mark.integration
def test_tool_registry_stats():
    """Test tool registry statistics."""
    stats = ToolRegistry.get_stats()
    
    assert "total_tools" in stats
    assert stats["total_tools"] > 0
    assert "categories" in stats
    assert len(stats["categories"]) > 0
    assert "tool_names" in stats


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_runtime_basic_execution():
    """Test basic agent runtime execution without LLM."""
    agent = AgentFactory.create_agent(
        id="test_agent",
        role="Test Agent",
        goal="Test execution",
        llm_model="gpt-4",
    )
    
    runtime = AgentRuntime(agent=agent)
    
    # Test that runtime is properly initialized
    assert runtime.agent.id == "test_agent"
    assert runtime._tools == {}
