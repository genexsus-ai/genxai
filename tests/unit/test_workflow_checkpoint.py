"""Tests for workflow checkpoint save/load and resume."""

from __future__ import annotations

import pytest

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.graph.nodes import NodeStatus
from genxai.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for checkpoint tests."""

    def __init__(self) -> None:
        super().__init__(model="mock-model", temperature=0.0)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
        self._update_stats(usage)
        return LLMResponse(content="Mock response", model=self.model, usage=usage)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs,
    ):
        yield "Mock "
        yield "response"


@pytest.mark.asyncio
async def test_checkpoint_round_trip_and_resume(tmp_path) -> None:
    agent = AgentFactory.create_agent(
        id="step",
        role="Checkpoint Agent",
        goal="Checkpoint workflow",
        llm_model="mock-model",
    )
    AgentRegistry.register(agent)

    graph = Graph(name="checkpoint_demo")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="step", agent_id="step"))
    graph.add_node(OutputNode())
    graph.add_edge(Edge(source="input", target="step"))
    graph.add_edge(Edge(source="step", target="output"))

    state = await graph.run(input_data={"payload": 1}, llm_provider=MockLLMProvider())
    state.pop("llm_provider", None)
    if isinstance(state.get("step"), dict):
        state["step"].pop("context", None)
    state.pop("output", None)

    # Persist checkpoint
    checkpoint_path = graph.save_checkpoint("first", state, tmp_path)
    assert checkpoint_path.exists()

    # Reset node status to simulate a fresh run
    for node in graph.nodes.values():
        node.status = NodeStatus.PENDING

    checkpoint = graph.load_checkpoint("first", tmp_path)
    resumed_state = await graph.run(
        input_data={"payload": 2},
        resume_from=checkpoint,
        llm_provider=MockLLMProvider(),
    )
    resumed_state.pop("llm_provider", None)

    assert resumed_state["input"]["payload"] == 2
    assert "step" in resumed_state