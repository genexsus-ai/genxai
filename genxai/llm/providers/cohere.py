"""Cohere LLM provider implementation."""

from typing import Any, Dict, Optional, AsyncIterator
import os
import logging

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class CohereProvider(LLMProvider):
    """Cohere LLM provider."""

    def __init__(
        self,
        model: str = "command",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Cohere provider.

        Args:
            model: Model name (command, command-light, command-r, command-r-plus)
            api_key: Cohere API key (defaults to COHERE_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Cohere-specific parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            logger.warning("Cohere API key not provided. Set COHERE_API_KEY environment variable.")
        
        self._client: Optional[Any] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere
            self._client = cohere.AsyncClient(api_key=self.api_key)
            logger.info(f"Cohere client initialized with model: {self.model}")
        except ImportError:
            logger.error(
                "Cohere package not installed. Install with: pip install cohere"
            )
            self._client = None
        except Exception as e:
            logger.error(f"Failed to initialize Cohere client: {e}")
            self._client = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Cohere.

        Args:
            prompt: User prompt
            system_prompt: System prompt (prepended to user prompt)
            **kwargs: Additional generation parameters

        Returns:
            LLM response

        Raises:
            RuntimeError: If client not initialized
            Exception: If API call fails
        """
        if not self._client:
            raise RuntimeError("Cohere client not initialized")

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        # Add additional parameters
        for key in ["p", "k", "frequency_penalty", "presence_penalty", "stop_sequences"]:
            if key in kwargs:
                params[key] = kwargs[key]

        try:
            logger.debug(f"Calling Cohere API with model: {self.model}")
            response = await self._client.generate(**params)

            # Extract response
            content = response.generations[0].text if response.generations else ""
            finish_reason = response.generations[0].finish_reason if response.generations else None

            # Extract usage (Cohere provides token counts in meta)
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
            if hasattr(response, 'meta') and response.meta:
                billed_units = response.meta.billed_units
                if billed_units:
                    usage["prompt_tokens"] = getattr(billed_units, 'input_tokens', 0)
                    usage["completion_tokens"] = getattr(billed_units, 'output_tokens', 0)
                    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

            # Update stats
            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    "generation_id": response.generations[0].id if response.generations else None,
                },
            )

        except Exception as e:
            logger.error(f"Cohere API call failed: {e}")
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
            raise RuntimeError("Cohere client not initialized")

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True,
        }
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        try:
            logger.debug(f"Streaming from Cohere API with model: {self.model}")
            
            response = await self._client.generate(**params)
            
            async for event in response:
                if event.event_type == "text-generation":
                    yield event.text

        except Exception as e:
            logger.error(f"Cohere streaming failed: {e}")
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
            raise RuntimeError("Cohere client not initialized")

        # Convert messages to Cohere chat format
        chat_history = []
        system_prompt = None
        last_user_message = ""
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                last_user_message = content
                # Add to history if not the last message
                if msg != messages[-1]:
                    chat_history.append({"role": "USER", "message": content})
            elif role == "assistant":
                chat_history.append({"role": "CHATBOT", "message": content})

        # Merge parameters
        params: Dict[str, Any] = {
            "model": self.model,
            "message": last_user_message,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if chat_history:
            params["chat_history"] = chat_history
        
        if system_prompt:
            params["preamble"] = system_prompt
        
        if self.max_tokens:
            params["max_tokens"] = kwargs.get("max_tokens", self.max_tokens)

        try:
            response = await self._client.chat(**params)

            content = response.text if hasattr(response, 'text') else ""
            finish_reason = response.finish_reason if hasattr(response, 'finish_reason') else None

            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
            if hasattr(response, 'meta') and response.meta:
                billed_units = response.meta.billed_units
                if billed_units:
                    usage["prompt_tokens"] = getattr(billed_units, 'input_tokens', 0)
                    usage["completion_tokens"] = getattr(billed_units, 'output_tokens', 0)
                    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

            self._update_stats(usage)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    "generation_id": response.generation_id if hasattr(response, 'generation_id') else None,
                },
            )

        except Exception as e:
            logger.error(f"Cohere chat API call failed: {e}")
            raise

    async def aclose(self) -> None:
        """Close Cohere client if initialized."""
        if not self._client:
            return

        close_fn = getattr(self._client, "close", None)
        if close_fn:
            result = close_fn()
            if hasattr(result, "__await__"):
                await result

        self._client = None
