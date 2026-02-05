"""Tests for LLM provider routing and fallback behavior."""

from __future__ import annotations

import pytest

from genxai.llm.base import LLMResponse, LLMProvider
from genxai.llm.factory import LLMProviderFactory
from genxai.llm.routing import RoutedLLMProvider


class FakeProvider(LLMProvider):
    def __init__(self, model: str, should_fail: bool = False, **kwargs) -> None:
        super().__init__(model=model)
        self.should_fail = should_fail

    async def generate(self, prompt: str, system_prompt: str | None = None, **kwargs):
        if self.should_fail:
            raise RuntimeError("fail")
        return LLMResponse(content=f"{self.model}:{prompt}", model=self.model, usage={"total_tokens": 1})

    async def generate_stream(self, prompt: str, system_prompt: str | None = None, **kwargs):
        if self.should_fail:
            raise RuntimeError("fail")
        yield f"{self.model}:{prompt}"


@pytest.mark.asyncio
async def test_routed_provider_fallbacks() -> None:
    primary = FakeProvider("primary", should_fail=True)
    fallback = FakeProvider("fallback")
    routed = RoutedLLMProvider(primary=primary, fallbacks=[fallback])

    response = await routed.generate("hello")
    assert response.content == "fallback:hello"


@pytest.mark.asyncio
async def test_routed_provider_streaming_fallback() -> None:
    primary = FakeProvider("primary", should_fail=True)
    fallback = FakeProvider("fallback")
    routed = RoutedLLMProvider(primary=primary, fallbacks=[fallback])

    chunks = []
    async for chunk in routed.generate_stream("hello"):
        chunks.append(chunk)
    assert chunks == ["fallback:hello"]


def test_factory_create_routed_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    class Primary(FakeProvider):
        pass

    class Backup(FakeProvider):
        pass

    LLMProviderFactory.register_provider("primary-model", Primary)
    LLMProviderFactory.register_provider("backup-model", Backup)

    provider = LLMProviderFactory.create_routed_provider(
        primary_model="primary-model",
        fallback_models=["backup-model"],
    )

    assert isinstance(provider, RoutedLLMProvider)