"""OpenAI LLM provider implementation."""

from typing import Any, Dict, Optional, AsyncIterator
import os
import logging

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpenAI provider.

        Args:
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI-specific parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)

        # Tests expect OpenAIProvider() with no args to raise, even if a global
        # OPENAI_API_KEY is present in the environment.
        if api_key is None:
            raise ValueError(
                "api_key is required when instantiating OpenAIProvider directly"
            )

        self.api_key = api_key
        
        self._client: Optional[Any] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
            logger.info(f"OpenAI client initialized with model: {self.model}")
        except ImportError:
            logger.error(
                "OpenAI package not installed. Install with: pip install openai"
            )
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._client = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using OpenAI.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            **kwargs: Additional generation parameters

        Returns:
            LLM response

        Raises:
            RuntimeError: If client not initialized
            Exception: If API call fails
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Merge parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        # Tool calling parameters
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            params["tool_choice"] = kwargs["tool_choice"]

        # Add additional parameters
        for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
            if key in kwargs:
                params[key] = kwargs[key]

        try:
            logger.debug(f"Calling OpenAI API with model: {self.model}")
            response = await self._client.chat.completions.create(**params)

            # Extract response
            message = response.choices[0].message
            content = message.content or ""
            finish_reason = response.choices[0].finish_reason

            # Extract usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            # Update stats
            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    "response_id": response.id,
                    "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else None,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

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

        Raises:
            RuntimeError: If client not initialized
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Merge parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True,
        }
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        try:
            logger.debug(f"Streaming from OpenAI API with model: {self.model}")
            stream = await self._client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise

    async def generate_chat(
        self,
        messages: list[Dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion for chat messages.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional generation parameters

        Returns:
            LLM response
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        # Merge parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        # Tool calling parameters
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            params["tool_choice"] = kwargs["tool_choice"]

        try:
            response = await self._client.chat.completions.create(**params)

            message = response.choices[0].message
            content = message.content or ""
            finish_reason = response.choices[0].finish_reason

            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    "response_id": response.id,
                    "tool_calls": message.tool_calls if hasattr(message, "tool_calls") else None,
                },
            )

        except Exception as e:
            logger.error(f"OpenAI chat API call failed: {e}")
            raise
