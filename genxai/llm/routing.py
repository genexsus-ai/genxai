"""Routing wrapper for LLM providers with fallback support."""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterable, List, Optional
import logging

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class RoutedLLMProvider(LLMProvider):
    """LLM provider wrapper that routes requests through fallback providers."""

    def __init__(
        self,
        primary: LLMProvider,
        fallbacks: Optional[Iterable[LLMProvider]] = None,
    ) -> None:
        self._primary = primary
        self._fallbacks = list(fallbacks or [])
        super().__init__(
            model=primary.model,
            temperature=primary.temperature,
            max_tokens=primary.max_tokens,
        )

    @property
    def providers(self) -> List[LLMProvider]:
        return [self._primary, *self._fallbacks]

    async def aclose(self) -> None:
        """Close all underlying providers."""
        for provider in self.providers:
            if hasattr(provider, "aclose"):
                await provider.aclose()
            elif hasattr(provider, "close"):
                provider.close()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        last_error: Optional[Exception] = None
        for provider in self.providers:
            try:
                response = await provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs,
                )
                self._update_stats(response.usage)
                return response
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Provider %s failed; attempting fallback: %s",
                    provider,
                    exc,
                )
                continue
        raise RuntimeError("All LLM providers failed") from last_error

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        last_error: Optional[Exception] = None
        for provider in self.providers:
            try:
                async for chunk in provider.generate_stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs,
                ):
                    yield chunk
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Streaming provider %s failed; attempting fallback: %s",
                    provider,
                    exc,
                )
                continue
        raise RuntimeError("All LLM providers failed for streaming") from last_error