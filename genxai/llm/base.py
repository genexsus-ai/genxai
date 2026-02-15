"""Base LLM provider interface."""

from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
import logging
import asyncio
import inspect

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")



class LLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM provider.

        Args:
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self._total_tokens = 0
        self._request_count = 0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion for prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional generation parameters

        Yields:
            Content chunks
        """
        pass

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion for chat messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        # Default implementation converts to single prompt
        prompt_parts = []
        system_prompt = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt = "\n".join(prompt_parts)
        return await self.generate(prompt, system_prompt, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "model": self.model,
            "total_tokens": self._total_tokens,
            "request_count": self._request_count,
            "avg_tokens_per_request": (
                self._total_tokens / self._request_count if self._request_count > 0 else 0
            ),
        }

    def reset_stats(self) -> None:
        """Reset provider statistics."""
        self._total_tokens = 0
        self._request_count = 0

    async def aclose(self) -> None:
        """Close any underlying async client resources."""
        client = getattr(self, "_client", None)
        if not client:
            return

        close_fn = getattr(client, "aclose", None)
        if close_fn:
            if inspect.iscoroutinefunction(close_fn):
                await close_fn()
            else:
                result = close_fn()
                if inspect.isawaitable(result):
                    await result
        else:
            close_fn = getattr(client, "close", None)
            if close_fn:
                if inspect.iscoroutinefunction(close_fn):
                    await close_fn()
                else:
                    result = close_fn()
                    if inspect.isawaitable(result):
                        await result

        self._client = None

    def close(self) -> None:
        """Synchronously close any underlying async client resources."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self.aclose())
            return

        if loop.is_closed():
            return
        loop.create_task(self.aclose())

    def _update_stats(self, usage: Dict[str, int]) -> None:
        """Update provider statistics.

        Args:
            usage: Token usage dictionary
        """
        self._request_count += 1
        self._total_tokens += usage.get("total_tokens", 0)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model})"

    def __del__(self) -> None:
        """Ensure clients are closed if possible."""
        try:
            self.close()
        except Exception:
            pass
