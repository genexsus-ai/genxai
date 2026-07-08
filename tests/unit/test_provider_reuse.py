"""Regression tests: LLM providers must survive aclose() + reuse.

AgentRuntime.execute() closes its provider in a finally block, which nulls
the underlying client. Flows (critic_review, p2p, ...) reuse the same runtime
across iterations, so the second iteration used to fail with
"<Provider> client not initialized". Providers now lazily re-initialize a
closed client via LLMProvider._ensure_client().
"""

import pytest

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.agent.runtime import AgentRuntime
from genxai.flows import CriticReviewFlow
from genxai.llm.base import LLMProvider, LLMResponse


@pytest.fixture(autouse=True)
def _clean_registry():
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


class FakeProvider(LLMProvider):
    """Provider that mimics the real close/reopen client lifecycle."""

    def __init__(self) -> None:
        super().__init__(model="fake-model", api_key="fake")
        self.generate_calls = 0
        self.reinit_count = 0
        self._initialize_client()

    def _initialize_client(self) -> None:
        self.reinit_count += 1
        self._client = object()  # stands in for AsyncOpenAI etc.

    async def generate(self, prompt, system_prompt=None, **kwargs):
        # Same guard pattern as the real providers
        self._ensure_client()
        if not self._client:
            raise RuntimeError("Fake client not initialized")
        self.generate_calls += 1
        return LLMResponse(
            content=f"draft-{self.generate_calls}",
            model=self.model,
            usage={"total_tokens": 5},
        )

    async def generate_stream(self, prompt, system_prompt=None, **kwargs):
        yield "chunk"

    async def generate_chat(self, messages, **kwargs):
        return await self.generate(prompt=str(messages))


class TestEnsureClient:
    def test_ensure_client_reopens_after_aclose(self):
        provider = FakeProvider()
        assert provider._client is not None

        # aclose() nulls the client (what AgentRuntime.execute's finally does)
        import asyncio

        asyncio.get_event_loop_policy()
        asyncio.run(provider.aclose())
        assert provider._client is None

        provider._ensure_client()
        assert provider._client is not None
        assert provider.reinit_count == 2

    def test_openai_provider_guard_calls_ensure(self):
        """The real provider guards must attempt re-init before raising."""
        import inspect

        from genxai.llm.providers.openai import OpenAIProvider

        source = inspect.getsource(OpenAIProvider)
        raises = source.count('raise RuntimeError("OpenAI client not initialized")')
        ensures = source.count("self._ensure_client()")
        assert raises > 0 and ensures == raises


class TestRuntimeReuse:
    @pytest.mark.asyncio
    async def test_runtime_execute_twice_reuses_provider(self):
        """execute() closes the provider; a second execute must still work."""
        agent = AgentFactory.create_agent(id="reuse_1", role="r", goal="g")
        provider = FakeProvider()
        runtime = AgentRuntime(agent=agent, llm_provider=provider, enable_memory=False)

        r1 = await runtime.execute("first task")
        assert provider._client is None  # closed by execute's finally
        r2 = await runtime.execute("second task")  # used to raise "not initialized"

        assert r1["status"] == r2["status"] == "completed"
        assert provider.generate_calls == 2

    @pytest.mark.asyncio
    async def test_critic_review_flow_multiple_iterations(self):
        """The original bug: critic_review with max_iterations=2 failed on
        iteration 2 because both runtimes' providers had been closed."""
        agents = [
            AgentFactory.create_agent(id="gen_1", role="generator", goal="draft"),
            AgentFactory.create_agent(id="crit_1", role="critic", goal="critique"),
        ]
        provider = FakeProvider()
        flow = CriticReviewFlow(agents, llm_provider=provider, max_iterations=2)

        state = await flow.run({"topic": "x"})

        assert len(state["drafts"]) == 2
        assert state["final"] == state["drafts"][-1]
        # generator + critic per iteration, all through the same provider
        assert provider.generate_calls == 4
