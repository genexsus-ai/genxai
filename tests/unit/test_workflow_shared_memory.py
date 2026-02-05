"""Tests for workflow-level shared memory wiring."""

import pytest
from typing import Any, Optional

from genxai.core.agent.base import Agent, AgentConfig
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.executor import WorkflowExecutor
from genxai.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for workflow tests."""

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
    ):
        yield "Mock "
        yield "response"


@pytest.mark.asyncio
async def test_workflow_executor_shared_memory_context_injected() -> None:
    agent = Agent(
        id="agent_one",
        config=AgentConfig(
            role="Agent One",
            goal="Test shared memory",
            llm_model="gpt-4",
            enable_memory=False,
        ),
    )
    AgentRegistry.register(agent)

    nodes = [
        {"id": "start", "type": "input"},
        {"id": "agent_one", "type": "agent"},
        {"id": "end", "type": "output"},
    ]
    edges = [
        {"source": "start", "target": "agent_one"},
        {"source": "agent_one", "target": "end"},
    ]

    executor = WorkflowExecutor(register_builtin_tools=False)

    result = await executor.execute(
        nodes=nodes,
        edges=edges,
        input_data={"task": "hello"},
        shared_memory=True,
        llm_provider=MockLLMProvider(),
    )

    assert result["status"] == "success"
    state = result["result"]
    assert "agent_one" in state
    context = state["agent_one"].get("context", {})
    assert "shared_memory" not in context