"""Ollama (local) LLM provider implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional, AsyncIterator
import logging
import os

import httpx

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local model execution.

    Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(
        self,
        model: str = "llama3",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        base_url: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Ollama provider.

        Args:
            model: Ollama model name (e.g., llama3, mistral)
            api_key: Optional API key (Ollama typically runs locally)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            base_url: Ollama server URL (default: http://localhost:11434)
            **kwargs: Additional Ollama-specific parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)
        self.api_key = api_key
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=kwargs.get("timeout", 120))

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        if system_prompt:
            payload["system"] = system_prompt
        if self.max_tokens:
            payload["options"]["num_predict"] = kwargs.get("max_tokens", self.max_tokens)

        # Merge any custom options
        if "options" in kwargs and isinstance(kwargs["options"], dict):
            payload["options"].update(kwargs["options"])

        logger.debug("Calling Ollama generate with model %s", self.model)
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()

        content = data.get("response", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": (data.get("prompt_eval_count", 0) + data.get("eval_count", 0)),
        }

        self._update_stats(usage)

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            finish_reason="stop",
            metadata={"done": data.get("done", True)},
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional generation parameters

        Yields:
            Content chunks
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }

        if system_prompt:
            payload["system"] = system_prompt
        if self.max_tokens:
            payload["options"]["num_predict"] = kwargs.get("max_tokens", self.max_tokens)
        if "options" in kwargs and isinstance(kwargs["options"], dict):
            payload["options"].update(kwargs["options"])

        logger.debug("Streaming from Ollama with model %s", self.model)
        async with self._client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = httpx.Response(200, content=line).json()
                chunk = data.get("response")
                if chunk:
                    yield chunk

    async def aclose(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()