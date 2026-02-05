"""Google Gemini LLM provider implementation."""

from typing import Any, Dict, Optional, AsyncIterator
import importlib
import os
import logging
import warnings

from genxai.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GoogleProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(
        self,
        model: str = "gemini-pro",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Google provider.

        Args:
            model: Model name (gemini-pro, gemini-pro-vision, gemini-ultra)
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Google-specific parameters
        """
        super().__init__(model, temperature, max_tokens, **kwargs)
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("Google API key not provided. Set GOOGLE_API_KEY environment variable.")
        
        self._client: Optional[Any] = None
        self._model_instance: Optional[Any] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Google Generative AI client."""
        try:
            genai = importlib.import_module("google.genai")

            if hasattr(genai, "configure"):
                genai.configure(api_key=self.api_key)

            if hasattr(genai, "GenerativeModel"):
                self._client = genai
                self._model_instance = genai.GenerativeModel(self.model)
                logger.info(f"Google Gemini client initialized with model: {self.model}")
                return

            if hasattr(genai, "Client"):
                self._client = genai.Client(api_key=self.api_key)
                models_attr = getattr(self._client, "models", None)
                if models_attr and hasattr(models_attr, "get"):
                    self._model_instance = models_attr.get(self.model)
                elif hasattr(self._client, "get_model"):
                    self._model_instance = self._client.get_model(self.model)
                else:
                    raise RuntimeError("google.genai client does not expose a model accessor")
                logger.info(f"Google Gemini client initialized with model: {self.model}")
                return

            raise RuntimeError("google.genai does not expose a known client API")
        except ImportError:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    category=FutureWarning,
                    module=r"google\.generativeai",
                )
                warnings.filterwarnings(
                    "ignore",
                    message=r"All support for the `google.generativeai` package has ended.*",
                    category=FutureWarning,
                )
                genai = importlib.import_module("google.generativeai")

            genai.configure(api_key=self.api_key)
            self._client = genai
            self._model_instance = genai.GenerativeModel(self.model)
            logger.info(f"Google Gemini client initialized with model: {self.model}")
        except ImportError:
            logger.error(
                "Google Generative AI package not installed. "
                "Install with: pip install google-genai"
            )
            self._client = None
            self._model_instance = None
        except Exception as e:
            logger.error(f"Failed to initialize Google client: {e}")
            self._client = None
            self._model_instance = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate completion using Gemini.

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
        if not self._model_instance:
            raise RuntimeError("Google Gemini client not initialized")

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Configure generation parameters
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        
        # Add additional parameters
        if "top_p" in kwargs:
            generation_config["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            generation_config["top_k"] = kwargs["top_k"]
        if "stop_sequences" in kwargs:
            generation_config["stop_sequences"] = kwargs["stop_sequences"]

        # Configure safety settings if provided
        safety_settings = kwargs.get("safety_settings")

        try:
            logger.debug(f"Calling Google Gemini API with model: {self.model}")
            
            response = await self._model_instance.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )

            # Extract response
            content = response.text if hasattr(response, 'text') else ""
            
            # Extract usage (Gemini doesn't always provide detailed token counts)
            usage = {
                "prompt_tokens": 0,  # Gemini API doesn't expose this directly
                "completion_tokens": 0,  # Gemini API doesn't expose this directly
                "total_tokens": 0,
            }
            
            # Try to get token count if available
            if hasattr(response, 'usage_metadata'):
                usage["prompt_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0)
                usage["completion_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0)
                usage["total_tokens"] = getattr(response.usage_metadata, 'total_token_count', 0)

            # Update stats
            self._update_stats(usage)

            # Get finish reason
            finish_reason = None
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={
                    "safety_ratings": (
                        [rating for candidate in response.candidates 
                         for rating in candidate.safety_ratings]
                        if hasattr(response, 'candidates') else []
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Google Gemini API call failed: {e}")
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
        if not self._model_instance:
            raise RuntimeError("Google Gemini client not initialized")

        # Combine system prompt with user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Configure generation parameters
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        safety_settings = kwargs.get("safety_settings")

        try:
            logger.debug(f"Streaming from Google Gemini API with model: {self.model}")
            
            response = await self._model_instance.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=True,
            )

            async for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Google Gemini streaming failed: {e}")
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
        if not self._model_instance:
            raise RuntimeError("Google Gemini client not initialized")

        # Convert messages to Gemini format
        # Gemini uses a simpler format: alternating user/model messages
        chat_history = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                chat_history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                chat_history.append({"role": "model", "parts": [content]})

        # Start chat session
        chat = self._model_instance.start_chat(history=chat_history[:-1] if chat_history else [])

        # Get last user message
        last_message = chat_history[-1]["parts"][0] if chat_history else ""
        
        # Prepend system prompt if provided
        if system_prompt:
            last_message = f"{system_prompt}\n\n{last_message}"

        # Configure generation
        generation_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        try:
            response = await chat.send_message_async(
                last_message,
                generation_config=generation_config,
            )

            content = response.text if hasattr(response, 'text') else ""

            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            
            if hasattr(response, 'usage_metadata'):
                usage["prompt_tokens"] = getattr(response.usage_metadata, 'prompt_token_count', 0)
                usage["completion_tokens"] = getattr(response.usage_metadata, 'candidates_token_count', 0)
                usage["total_tokens"] = getattr(response.usage_metadata, 'total_token_count', 0)

            self._update_stats(usage)

            finish_reason = None
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = str(response.candidates[0].finish_reason)

            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                finish_reason=finish_reason,
                metadata={},
            )

        except Exception as e:
            logger.error(f"Google Gemini chat API call failed: {e}")
            raise
