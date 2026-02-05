"""Anthropic Claude LLM provider implementation."""

from typing import Any, Dict, Optional, AsyncIterator
import os
import logging

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    _MODEL_ALIASES = {
        # Claude 4.5 models
        "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5": "claude-haiku-4-5-20251001",
        "claude-opus-4-5": "claude-opus-4-5-20251101",
        # Claude 4 models
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-opus-4": "claude-opus-4-20250514",
        "claude-opus-4-1": "claude-opus-4-1-20250805",
        # Claude 3.5 models
        "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
        # Claude 3 models
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
    }

    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Anthropic provider.

        Args:
            model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic-specific parameters
        """
        resolved_model = self._normalize_model(model)
        super().__init__(resolved_model, temperature, max_tokens, **kwargs)
        self.requested_model = model
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
        
        self._client: Optional[Any] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
            logger.info(f"Anthropic client initialized with model: {self.model}")
        except ImportError:
            logger.error(
                "Anthropic package not installed. Install with: pip install anthropic"
            )
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            self._client = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Claude.

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
            raise RuntimeError("Anthropic client not initialized")

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens or 1024),
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt

        # Add additional parameters
        for key in ["top_p", "top_k", "stop_sequences"]:
            if key in kwargs:
                params[key] = kwargs[key]

        try:
            logger.debug(f"Calling Anthropic API with model: {self.model}")
            response = await self._client.messages.create(**params)

            # Extract response
            content = response.content[0].text if response.content else ""
            finish_reason = response.stop_reason

            # Extract usage
            usage = {
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
                "total_tokens": (
                    (response.usage.input_tokens + response.usage.output_tokens)
                    if response.usage else 0
                ),
            }

            # Update stats
            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={"response_id": response.id, "type": response.type},
            )

        except Exception as e:
            if self._is_model_not_found_error(e):
                fallback_model = self._fallback_model(self.model)
                if fallback_model and fallback_model != self.model:
                    logger.warning(
                        "Anthropic model '%s' not found. Falling back to '%s'.",
                        self.model,
                        fallback_model,
                    )
                    self.model = fallback_model
                    params["model"] = fallback_model
                    response = await self._client.messages.create(**params)
                    content = response.content[0].text if response.content else ""
                    finish_reason = response.stop_reason
                    usage = {
                        "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                        "completion_tokens": response.usage.output_tokens if response.usage else 0,
                        "total_tokens": (
                            (response.usage.input_tokens + response.usage.output_tokens)
                            if response.usage else 0
                        ),
                    }
                    self._update_stats(usage)
                    return LLMResponse(
                        content=content,
                        model=response.model,
                        usage=usage,
                        finish_reason=finish_reason,
                        metadata={"response_id": response.id, "type": response.type},
                    )
            logger.error(f"Anthropic API call failed: {e}")
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
            raise RuntimeError("Anthropic client not initialized")

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens or 1024),
            "stream": True,
        }
        
        # Add system prompt if provided
        if system_prompt:
            params["system"] = system_prompt

        try:
            logger.debug(f"Streaming from Anthropic API with model: {self.model}")
            
            async with self._client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
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
            raise RuntimeError("Anthropic client not initialized")

        # Extract system prompt if present
        system_prompt = None
        chat_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                chat_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens or 1024),
        }
        
        if system_prompt:
            params["system"] = system_prompt

        try:
            response = await self._client.messages.create(**params)

            content = response.content[0].text if response.content else ""
            finish_reason = response.stop_reason

            usage = {
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
                "total_tokens": (
                    (response.usage.input_tokens + response.usage.output_tokens)
                    if response.usage else 0
                ),
            }

            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={"response_id": response.id, "type": response.type},
            )

        except Exception as e:
            if self._is_model_not_found_error(e):
                fallback_model = self._fallback_model(self.model)
                if fallback_model and fallback_model != self.model:
                    logger.warning(
                        "Anthropic model '%s' not found. Falling back to '%s'.",
                        self.model,
                        fallback_model,
                    )
                    self.model = fallback_model
                    params["model"] = fallback_model
                    response = await self._client.messages.create(**params)
                    content = response.content[0].text if response.content else ""
                    finish_reason = response.stop_reason
                    usage = {
                        "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                        "completion_tokens": response.usage.output_tokens if response.usage else 0,
                        "total_tokens": (
                            (response.usage.input_tokens + response.usage.output_tokens)
                            if response.usage else 0
                        ),
                    }
                    self._update_stats(usage)
                    return LLMResponse(
                        content=content,
                        model=response.model,
                        usage=usage,
                        finish_reason=finish_reason,
                        metadata={"response_id": response.id, "type": response.type},
                    )
            logger.error(f"Anthropic chat API call failed: {e}")
            raise

    @classmethod
    def _normalize_model(cls, model: str) -> str:
        model_key = model.strip().lower()
        return cls._MODEL_ALIASES.get(model_key, model)

    @staticmethod
    def _is_model_not_found_error(error: Exception) -> bool:
        message = str(error).lower()
        return "not_found_error" in message or "model:" in message

    @staticmethod
    def _fallback_model(model: str) -> Optional[str]:
        model_lower = model.lower()
        # Claude 4.5 fallbacks
        if model_lower.startswith("claude-sonnet-4-5") or model_lower.startswith("claude-opus-4-5"):
            return "claude-sonnet-4-20250514"
        if model_lower.startswith("claude-haiku-4-5"):
            return "claude-haiku-4-5-20251001"
        # Claude 4 fallbacks
        if model_lower.startswith("claude-opus-4"):
            return "claude-sonnet-4-20250514"
        if model_lower.startswith("claude-sonnet-4"):
            return "claude-3-5-sonnet-20241022"
        # Claude 3.5 fallbacks
        if model_lower.startswith("claude-3-5"):
            return "claude-3-sonnet-20240229"
        # Claude 3 fallbacks
        if model_lower.startswith("claude-3-opus"):
            return "claude-3-sonnet-20240229"
        if model_lower.startswith("claude-3-sonnet"):
            return "claude-3-haiku-20240307"
        if model_lower.startswith("claude-3-haiku"):
            return "claude-3-haiku-20240307"
        # Generic Claude fallback
        if model_lower.startswith("claude"):
            return "claude-3-haiku-20240307"
        return None
