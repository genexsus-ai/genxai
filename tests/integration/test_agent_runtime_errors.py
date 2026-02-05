"""Offline integration tests for AgentRuntime error paths."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from genxai.core.agent.base import Agent, AgentConfig
from genxai.core.agent.runtime import AgentRuntime, AgentExecutionError
from genxai.llm.base import LLMResponse


class FailingLLMProvider:
    """LLM provider that fails for a configurable number of calls."""

    def __init__(self, fail_times: int = 1) -> None:
        self.fail_times = fail_times
        self.calls = 0

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("Injected LLM failure")
        return LLMResponse(
            content="Recovered",
            model="stub",
            usage={"total_tokens": 1, "prompt_tokens": 1, "completion_tokens": 0},
        )


class SlowLLMProvider:
    """LLM provider that sleeps long enough to trigger timeouts."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        await asyncio.sleep(0.5)
        return LLMResponse(
            content="Slow",
            model="stub",
            usage={"total_tokens": 1, "prompt_tokens": 1, "completion_tokens": 0},
        )


class BrokenTool:
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        raise RuntimeError("Tool exploded")


def _make_agent(tools: list[str] | None = None) -> Agent:
    config = AgentConfig(
        role="Tester",
        goal="Exercise error paths",
        llm_model="stub",
        tools=tools or [],
    )
    return Agent(id="agent_error", config=config)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_exhaustion_raises_agent_execution_error() -> None:
    """Retry exhaustion should surface as AgentExecutionError."""
    agent = _make_agent()
    runtime = AgentRuntime(agent=agent, llm_provider=FailingLLMProvider(fail_times=10))

    with pytest.raises(AgentExecutionError):
        await runtime.execute("fail please")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retry_eventually_succeeds() -> None:
    """Retries should recover when provider succeeds after failures."""
    agent = _make_agent()
    runtime = AgentRuntime(agent=agent, llm_provider=FailingLLMProvider(fail_times=2))

    result = await runtime.execute("recover please")
    assert result["status"] == "completed"
    assert result["output"] == "Recovered"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_timeout_raises_timeout() -> None:
    """Timeouts should propagate as asyncio.TimeoutError."""
    agent = _make_agent()
    runtime = AgentRuntime(agent=agent, llm_provider=SlowLLMProvider())

    with pytest.raises(asyncio.TimeoutError):
        await runtime.execute("timeout", timeout=0.05)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_failure_still_returns_response() -> None:
    """Tool failures should be reflected in tool results but not crash execution."""
    agent = _make_agent(tools=["broken_tool"])
    runtime = AgentRuntime(agent=agent, llm_provider=FailingLLMProvider(fail_times=0))
    runtime.set_tools({"broken_tool": BrokenTool()})

    # Force tool invocation in response so _process_tools runs.
    runtime._process_tools = AgentRuntime._process_tools.__get__(runtime)
    runtime._parse_tool_calls = lambda response: [
        {"name": "broken_tool", "arguments": {}}
    ]
    async def _format_stub(original: str, results: list[Dict[str, Any]]) -> str:
        return "TOOL_ERROR"

    runtime._format_tool_results = _format_stub

    result = await runtime.execute("run tool")
    assert result["status"] == "completed"
    assert result["output"] == "TOOL_ERROR"