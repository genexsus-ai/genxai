"""Offline integration tests for workflows without external LLM APIs."""

from __future__ import annotations

import pytest
from typing import Any, AsyncIterator, Dict, List

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.graph.engine import Graph, GraphExecutionError
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.memory.manager import MemorySystem
from genxai.llm.base import LLMProvider, LLMResponse
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin.computation.calculator import CalculatorTool


class StubLLMProvider(LLMProvider):
    """Deterministic LLM provider for offline tests."""

    def __init__(self) -> None:
        super().__init__(model="stub", temperature=0.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        content = f"STUB_RESPONSE: {prompt[:100]}"
        usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        self._update_stats(usage)
        return LLMResponse(content=content, model="stub", usage=usage)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        for chunk in ["STUB", "_", "STREAM"]:
            yield chunk


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_agent_with_tools():
    """Run an agent with a tool using stubbed LLM output."""
    agent = AgentFactory.create_agent(
        id="offline_agent",
        role="Tool User",
        goal="Use tools",
        tools=["calculator"],
        llm_model="stub",
    )
    runtime = AgentRuntime(agent=agent, llm_provider=StubLLMProvider())
    runtime.set_tools({"calculator": CalculatorTool()})

    result = await runtime.execute("Use calculator to compute 2+2")
    assert result["status"] == "completed"
    assert "STUB_RESPONSE" in result["output"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_workflow_graph_executes():
    """Ensure graph engine can execute with stubbed agent runtime."""
    agent = AgentFactory.create_agent(
        id="graph_agent",
        role="Graph Agent",
        goal="Process workflow",
        llm_model="stub",
    )
    runtime = AgentRuntime(agent=agent, llm_provider=StubLLMProvider())

    graph = Graph(name="offline_workflow")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="agent", agent_id=agent.id, agent=agent))
    graph.add_node(OutputNode())
    graph.add_edge(Edge(source="input", target="agent"))
    graph.add_edge(Edge(source="agent", target="output"))

    # Inject runtime directly for this test.
    runtime.set_memory(MemorySystem(agent_id=agent.id))
    state = await graph.run(input_data={"message": "hello"}, llm_provider=StubLLMProvider())

    assert "input" in state
    assert "agent" in state


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_memory_integration(tmp_path):
    """Ensure memory persistence can be used in offline workflows."""
    memory = MemorySystem(
        agent_id="memory_agent",
        persistence_enabled=True,
        persistence_path=tmp_path,
    )
    agent = AgentFactory.create_agent(
        id="memory_agent",
        role="Memory Agent",
        goal="Remember details",
        llm_model="stub",
        enable_memory=True,
    )
    runtime = AgentRuntime(agent=agent, llm_provider=StubLLMProvider())
    runtime.set_memory(memory)

    result1 = await runtime.execute("Remember this value: Orion")
    result2 = await runtime.execute("What did I just ask you to remember?")

    assert result1["status"] == "completed"
    assert result2["status"] == "completed"
    stats = await memory.get_stats()
    assert stats["persistence"]["enabled"] is True


@pytest.mark.integration
def test_tool_registry_offline():
    """Ensure tool registry can be used without LLM setup."""
    ToolRegistry.register(CalculatorTool())
    tool = ToolRegistry.get("calculator")
    assert tool is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_branching_workflow():
    """Ensure conditional branching executes the expected path."""
    agent_a = AgentFactory.create_agent(
        id="agent_a",
        role="Branch A Agent",
        goal="Handle branch A",
        llm_model="stub",
    )
    agent_b = AgentFactory.create_agent(
        id="agent_b",
        role="Branch B Agent",
        goal="Handle branch B",
        llm_model="stub",
    )
    AgentRegistry.register(agent_a)
    AgentRegistry.register(agent_b)

    graph = Graph(name="offline_branching")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="branch_a", agent_id="agent_a"))
    graph.add_node(AgentNode(id="branch_b", agent_id="agent_b"))
    graph.add_node(OutputNode())

    graph.add_edge(Edge(source="input", target="branch_a", condition=lambda s: s["input"]["route"] == "A"))
    graph.add_edge(Edge(source="input", target="branch_b", condition=lambda s: s["input"]["route"] == "B"))
    graph.add_edge(Edge(source="branch_a", target="output"))
    graph.add_edge(Edge(source="branch_b", target="output"))

    state = await graph.run(input_data={"route": "A"}, llm_provider=StubLLMProvider())
    assert "branch_a" in state
    assert "branch_b" not in state


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_parallel_workflow():
    """Ensure parallel edges execute concurrently."""
    agent_1 = AgentFactory.create_agent(
        id="worker_1",
        role="Worker 1",
        goal="Handle parallel work",
        llm_model="stub",
    )
    agent_2 = AgentFactory.create_agent(
        id="worker_2",
        role="Worker 2",
        goal="Handle parallel work",
        llm_model="stub",
    )
    AgentRegistry.register(agent_1)
    AgentRegistry.register(agent_2)

    graph = Graph(name="offline_parallel")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="worker_1", agent_id="worker_1"))
    graph.add_node(AgentNode(id="worker_2", agent_id="worker_2"))
    graph.add_node(OutputNode())

    graph.add_edge(Edge(source="input", target="worker_1", metadata={"parallel": True}))
    graph.add_edge(Edge(source="input", target="worker_2", metadata={"parallel": True}))
    graph.add_edge(Edge(source="worker_1", target="output"))
    graph.add_edge(Edge(source="worker_2", target="output"))

    state = await graph.run(input_data={"task": "parallel"}, llm_provider=StubLLMProvider())
    assert "worker_1" in state
    assert "worker_2" in state


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_cyclic_workflow_guard():
    """Ensure cyclic workflows do not re-run completed nodes endlessly."""
    loop_agent = AgentFactory.create_agent(
        id="loop",
        role="Loop Agent",
        goal="Cycle through the workflow",
        llm_model="stub",
    )
    AgentRegistry.register(loop_agent)

    graph = Graph(name="offline_cycle")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="loop", agent_id="loop"))

    graph.add_edge(Edge(source="input", target="loop"))
    graph.add_edge(Edge(source="loop", target="loop"))

    state = await graph.run(
        input_data={"task": "loop"},
        max_iterations=3,
        llm_provider=StubLLMProvider(),
    )
    assert state["iterations"] <= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_edge_priority_ordering():
    """Ensure sequential edges respect priority ordering (lower priority runs first)."""
    first_agent = AgentFactory.create_agent(
        id="first",
        role="First Agent",
        goal="Run first",
        llm_model="stub",
    )
    second_agent = AgentFactory.create_agent(
        id="second",
        role="Second Agent",
        goal="Run second",
        llm_model="stub",
    )
    AgentRegistry.register(first_agent)
    AgentRegistry.register(second_agent)

    graph = Graph(name="offline_priority")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="first", agent_id="first"))
    graph.add_node(AgentNode(id="second", agent_id="second"))
    graph.add_node(OutputNode())

    graph.add_edge(Edge(source="input", target="first", priority=0))
    graph.add_edge(Edge(source="input", target="second", priority=5))
    graph.add_edge(Edge(source="first", target="output"))
    graph.add_edge(Edge(source="second", target="output"))

    state = await graph.run(input_data={"task": "priority"}, llm_provider=StubLLMProvider())
    ordered = [key for key in state.keys() if key in {"first", "second"}]
    assert ordered == ["first", "second"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_offline_conditional_metadata_parallel():
    """Ensure conditional + parallel edge metadata is honored."""
    allowed_agent = AgentFactory.create_agent(
        id="allowed",
        role="Allowed Agent",
        goal="Run when allowed",
        llm_model="stub",
    )
    blocked_agent = AgentFactory.create_agent(
        id="blocked",
        role="Blocked Agent",
        goal="Run when blocked",
        llm_model="stub",
    )
    AgentRegistry.register(allowed_agent)
    AgentRegistry.register(blocked_agent)

    graph = Graph(name="offline_conditional_parallel")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="allowed", agent_id="allowed"))
    graph.add_node(AgentNode(id="blocked", agent_id="blocked"))
    graph.add_node(OutputNode())

    graph.add_edge(
        Edge(
            source="input",
            target="allowed",
            metadata={"parallel": True},
            condition=lambda s: s["input"]["run"] is True,
        )
    )
    graph.add_edge(
        Edge(
            source="input",
            target="blocked",
            metadata={"parallel": True},
            condition=lambda s: s["input"]["run"] is False,
        )
    )
    graph.add_edge(Edge(source="allowed", target="output"))
    graph.add_edge(Edge(source="blocked", target="output"))

    state = await graph.run(input_data={"run": True}, llm_provider=StubLLMProvider())
    assert "allowed" in state
    assert "blocked" not in state