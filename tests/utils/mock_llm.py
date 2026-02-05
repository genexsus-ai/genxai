"""Mock LLM provider for tests."""

from typing import Any, AsyncIterator, Optional

from genxai.llm.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for tests."""

    def __init__(
        self,
        model: str = "mock-model",
        temperature: float = 0.0,
        response_text: str = (
            "Mock response for testing purposes. This is a deterministic placeholder."
        ),
    ) -> None:
        super().__init__(model=model, temperature=temperature)
        self._response_text = response_text

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        content = self._response_text
        usage = {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}
        self._update_stats(usage)
        return LLMResponse(content=content, model=self.model, usage=usage, finish_reason="stop")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        yield "Mock "
        yield "response"