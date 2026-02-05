"""Unit tests for graph components."""

import pytest
from typing import Any, AsyncIterator, Optional

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.nodes import Node, NodeType, NodeConfig, InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge, ConditionalEdge
from genxai.core.graph.engine import Graph, GraphExecutionError
from genxai.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for graph tests."""

    def __init__(self) -> None:
        super().__init__(model="mock-model", temperature=0.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
        self._update_stats(usage)
        return LLMResponse(content="Mock response", model=self.model, usage=usage)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        yield "Mock "
        yield "response"


class TestNode:
    """Tests for Node class."""

    def test_node_creation(self) -> None:
        """Test basic node creation."""
        node = Node(
            id="test_node",
            type=NodeType.AGENT,
            config=NodeConfig(type=NodeType.AGENT, data={"agent_id": "agent_1"}),
        )
        assert node.id == "test_node"
        assert node.type == NodeType.AGENT
        assert node.config.data["agent_id"] == "agent_1"

    def test_input_node(self) -> None:
        """Test InputNode creation."""
        node = InputNode()
        assert node.id == "input"
        assert node.type == NodeType.INPUT

    def test_output_node(self) -> None:
        """Test OutputNode creation."""
        node = OutputNode()
        assert node.id == "output"
        assert node.type == NodeType.OUTPUT

    def test_agent_node(self) -> None:
        """Test AgentNode creation."""
        node = AgentNode(id="agent_1", agent_id="my_agent")
        assert node.id == "agent_1"
        assert node.type == NodeType.AGENT
        assert node.config.data["agent_id"] == "my_agent"


class TestEdge:
    """Tests for Edge class."""

    def test_edge_creation(self) -> None:
        """Test basic edge creation."""
        edge = Edge(source="node1", target="node2")
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.condition is None

    def test_conditional_edge(self) -> None:
        """Test ConditionalEdge creation."""
        condition = lambda state: state.get("value", 0) > 10
        edge = ConditionalEdge(source="node1", target="node2", condition=condition)
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.condition is not None

    def test_edge_condition_evaluation(self) -> None:
        """Test edge condition evaluation."""
        condition = lambda state: state.get("value", 0) > 10
        edge = ConditionalEdge(source="node1", target="node2", condition=condition)

        assert edge.evaluate_condition({"value": 15}) is True
        assert edge.evaluate_condition({"value": 5}) is False
        assert edge.evaluate_condition({}) is False


class TestGraph:
    """Tests for Graph class."""

    def test_graph_creation(self) -> None:
        """Test basic graph creation."""
        graph = Graph(name="test_workflow")
        assert graph.name == "test_workflow"
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self) -> None:
        """Test adding nodes to graph."""
        graph = Graph()
        node = InputNode()
        graph.add_node(node)

        assert len(graph.nodes) == 1
        assert "input" in graph.nodes
        assert graph.get_node("input") == node

    def test_add_duplicate_node(self) -> None:
        """Test that adding duplicate node raises error."""
        graph = Graph()
        node1 = InputNode()
        node2 = InputNode()

        graph.add_node(node1)
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node(node2)

    def test_add_edge(self) -> None:
        """Test adding edges to graph."""
        graph = Graph()
        node1 = InputNode()
        node2 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)

        edge = Edge(source="input", target="output")
        graph.add_edge(edge)

        assert len(graph.edges) == 1
        assert len(graph.get_outgoing_edges("input")) == 1

    def test_add_edge_invalid_nodes(self) -> None:
        """Test that adding edge with invalid nodes raises error."""
        graph = Graph()
        edge = Edge(source="nonexistent1", target="nonexistent2")

        with pytest.raises(ValueError, match="not found"):
            graph.add_edge(edge)

    def test_graph_validation(self) -> None:
        """Test graph validation."""
        graph = Graph()
        node1 = InputNode()
        node2 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(Edge(source="input", target="output"))

        assert graph.validate() is True

    def test_empty_graph_validation(self) -> None:
        """Test that empty graph fails validation."""
        graph = Graph()
        with pytest.raises(GraphExecutionError, match="at least one node"):
            graph.validate()

    def test_get_outgoing_edges(self) -> None:
        """Test getting outgoing edges."""
        graph = Graph()
        node1 = InputNode()
        node2 = OutputNode()
        node3 = AgentNode(id="agent1", agent_id="test_agent")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(Edge(source="input", target="agent1"))
        graph.add_edge(Edge(source="input", target="output"))

        outgoing = graph.get_outgoing_edges("input")
        assert len(outgoing) == 2

    def test_get_incoming_nodes(self) -> None:
        """Test getting incoming nodes."""
        graph = Graph()
        node1 = InputNode()
        node2 = AgentNode(id="agent1", agent_id="test_agent")
        node3 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(Edge(source="input", target="output"))
        graph.add_edge(Edge(source="agent1", target="output"))

        incoming = graph.get_incoming_nodes("output")
        assert len(incoming) == 2
        assert "input" in incoming
        assert "agent1" in incoming

    def test_topological_sort(self) -> None:
        """Test topological sort."""
        graph = Graph()
        node1 = InputNode()
        node2 = AgentNode(id="agent1", agent_id="test_agent")
        node3 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(Edge(source="input", target="agent1"))
        graph.add_edge(Edge(source="agent1", target="output"))

        sorted_nodes = graph.topological_sort()
        assert len(sorted_nodes) == 3
        assert sorted_nodes.index("input") < sorted_nodes.index("agent1")
        assert sorted_nodes.index("agent1") < sorted_nodes.index("output")

    def test_to_dict(self) -> None:
        """Test graph serialization to dict."""
        graph = Graph(name="test_graph")
        node1 = InputNode()
        node2 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(Edge(source="input", target="output"))

        graph_dict = graph.to_dict()
        assert graph_dict["name"] == "test_graph"
        assert len(graph_dict["nodes"]) == 2
        assert len(graph_dict["edges"]) == 1

    @pytest.mark.asyncio
    async def test_simple_graph_execution(self) -> None:
        """Test simple graph execution."""
        graph = Graph(name="simple_test")
        node1 = InputNode()
        node2 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(Edge(source="input", target="output"))

        result = await graph.run(input_data="test_input")
        assert "input" in result
        assert result["input"] == "test_input"

    @pytest.mark.asyncio
    async def test_conditional_edge_execution(self) -> None:
        """Test graph execution with conditional edges."""
        agent1 = AgentFactory.create_agent(
            id="test_agent",
            role="Agent 1",
            goal="Test conditional edge",
            llm_model="mock-model",
        )
        agent2 = AgentFactory.create_agent(
            id="test_agent2",
            role="Agent 2",
            goal="Test conditional edge",
            llm_model="mock-model",
        )
        AgentRegistry.register(agent1)
        AgentRegistry.register(agent2)

        graph = Graph(name="conditional_test")
        node1 = InputNode()
        node2 = AgentNode(id="agent1", agent_id="test_agent")
        node3 = AgentNode(id="agent2", agent_id="test_agent2")
        node4 = OutputNode()

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        graph.add_node(node4)

        graph.add_edge(Edge(source="input", target="agent1"))
        graph.add_edge(
            ConditionalEdge(
                source="agent1", target="agent2", condition=lambda s: s.get("value", 0) > 5
            )
        )
        graph.add_edge(Edge(source="agent2", target="output"))

        result = await graph.run(
            input_data={"value": 10},
            llm_provider=MockLLMProvider(),
        )
        assert "input" in result
