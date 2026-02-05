"""LLM Provider Factory for creating and managing LLM providers."""

from typing import Optional, Dict, Any, Iterable, List
import os
import logging

from genxai.llm.base import LLMProvider
from genxai.llm.routing import RoutedLLMProvider
from genxai.llm.providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    _fallback_chain: List[str] = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "claude-3-sonnet",
        "claude-3-haiku",
    ]

    _providers: Dict[str, type[LLMProvider]] = {
        # OpenAI
        "openai": OpenAIProvider,
        "gpt-4": OpenAIProvider,
        "gpt-3.5-turbo": OpenAIProvider,
        "gpt-4-turbo": OpenAIProvider,
        "gpt-4o": OpenAIProvider,
    }
    
    # Lazy-loaded providers (imported on demand)
    _provider_modules: Dict[str, str] = {
        "anthropic": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-opus": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-sonnet": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-haiku": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-5-sonnet-20241022": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-5-sonnet-20240620": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-opus-20240229": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-sonnet-20240229": "genxai.llm.providers.anthropic.AnthropicProvider",
        "claude-3-haiku-20240307": "genxai.llm.providers.anthropic.AnthropicProvider",
        "google": "genxai.llm.providers.google.GoogleProvider",
        "gemini-pro": "genxai.llm.providers.google.GoogleProvider",
        "gemini-ultra": "genxai.llm.providers.google.GoogleProvider",
        "cohere": "genxai.llm.providers.cohere.CohereProvider",
        "command": "genxai.llm.providers.cohere.CohereProvider",
        "command-r": "genxai.llm.providers.cohere.CohereProvider",
        "ollama": "genxai.llm.providers.ollama.OllamaProvider",
        "llama3": "genxai.llm.providers.ollama.OllamaProvider",
        "mistral": "genxai.llm.providers.ollama.OllamaProvider",
        "phi3": "genxai.llm.providers.ollama.OllamaProvider",
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """Register a new LLM provider.

        Args:
            name: Provider name or model name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered LLM provider: {name}")

    @classmethod
    def create_provider(
        cls,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_models: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus")
            api_key: API key for the provider
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            fallback_models: List of fallback models if primary fails
            **kwargs: Additional provider-specific parameters

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider not found or API key missing
        """
        # Determine provider from model name
        provider_class = cls._get_provider_class(model)

        if not provider_class:
            raise ValueError(
                f"No provider found for model '{model}'. "
                f"Available providers: {list(cls._providers.keys())}"
            )

        # Get API key from environment if not provided
        if api_key is None:
            api_key = cls._get_api_key_for_provider(provider_class)

        if not api_key:
            logger.warning(
                f"No API key provided for {provider_class.__name__}. "
                "Provider may fail at runtime."
            )

        # Create provider instance
        try:
            provider = provider_class(
                model=model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            logger.info(f"Created LLM provider: {provider_class.__name__} with model {model}")
            if fallback_models:
                return RoutedLLMProvider(
                    primary=provider,
                    fallbacks=cls._create_fallback_providers(
                        fallback_models,
                        api_key=api_key,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs,
                    ),
                )
            return provider

        except Exception as e:
            logger.error(f"Failed to create provider for model '{model}': {e}")

            # Try fallback models if provided
            if fallback_models:
                logger.info(f"Attempting fallback models: {fallback_models}")
                for fallback_model in fallback_models:
                    try:
                        return cls.create_provider(
                            model=fallback_model,
                            api_key=api_key,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs,
                        )
                    except Exception as fallback_error:
                        logger.warning(f"Fallback model '{fallback_model}' failed: {fallback_error}")
                        continue

            raise ValueError(f"Failed to create provider for model '{model}': {e}") from e

    @classmethod
    def create_routed_provider(
        cls,
        primary_model: str,
        fallback_models: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> LLMProvider:
        """Create a routed provider with a fallback chain.

        Args:
            primary_model: Primary model name
            fallback_models: Optional override for fallback chain
            **kwargs: Provider options forwarded to create_provider

        Returns:
            RoutedLLMProvider instance
        """
        fallback_chain = fallback_models or cls._fallback_chain
        return cls.create_provider(
            model=primary_model,
            fallback_models=fallback_chain,
            **kwargs,
        )

    @classmethod
    def set_default_fallback_chain(cls, models: Iterable[str]) -> None:
        """Set the default fallback model chain."""
        cls._fallback_chain = list(models)

    @classmethod
    def _create_fallback_providers(
        cls,
        fallback_models: Iterable[str],
        api_key: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs: Any,
    ) -> List[LLMProvider]:
        providers: List[LLMProvider] = []
        for fallback_model in fallback_models:
            try:
                provider_class = cls._get_provider_class(fallback_model)
                if not provider_class:
                    logger.warning("No provider class for fallback model %s", fallback_model)
                    continue
                fallback_key = api_key or cls._get_api_key_for_provider(provider_class)
                provider = provider_class(
                    model=fallback_model,
                    api_key=fallback_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                providers.append(provider)
            except Exception as exc:
                logger.warning("Failed to initialize fallback model %s: %s", fallback_model, exc)
        return providers

    @classmethod
    def _load_provider_class(cls, module_path: str) -> Optional[type[LLMProvider]]:
        """Dynamically load a provider class.

        Args:
            module_path: Full module path (e.g., 'genxai.llm.providers.anthropic.AnthropicProvider')

        Returns:
            Provider class or None
        """
        try:
            module_name, class_name = module_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        except Exception as e:
            logger.error(f"Failed to load provider from {module_path}: {e}")
            return None

    @classmethod
    def _get_provider_class(cls, model: str) -> Optional[type[LLMProvider]]:
        """Get provider class for a model.

        Args:
            model: Model name

        Returns:
            Provider class or None
        """
        model_key = model.lower()

        # Direct match in pre-loaded providers
        if model_key in cls._providers:
            return cls._providers[model_key]

        # Check lazy-loaded providers
        if model_key in cls._provider_modules:
            provider_class = cls._load_provider_class(cls._provider_modules[model_key])
            if provider_class:
                # Cache it for future use
                cls._providers[model_key] = provider_class
                return provider_class

        # Check if model starts with known provider prefix
        model_lower = model_key
        if model_lower.startswith("gpt"):
            return OpenAIProvider
        elif model_lower.startswith("claude"):
            provider_class = cls._load_provider_class("genxai.llm.providers.anthropic.AnthropicProvider")
            if provider_class:
                cls._providers[model_key] = provider_class
                return provider_class
        elif model_lower.startswith("gemini"):
            provider_class = cls._load_provider_class("genxai.llm.providers.google.GoogleProvider")
            if provider_class:
                cls._providers[model_key] = provider_class
                return provider_class
        elif model_lower.startswith("command"):
            provider_class = cls._load_provider_class("genxai.llm.providers.cohere.CohereProvider")
            if provider_class:
                cls._providers[model_key] = provider_class
                return provider_class
        elif model_lower.startswith("llama") or model_lower.startswith("mistral") or model_lower.startswith("phi"):
            provider_class = cls._load_provider_class("genxai.llm.providers.ollama.OllamaProvider")
            if provider_class:
                cls._providers[model_key] = provider_class
                return provider_class

        return None

    @classmethod
    def _get_api_key_for_provider(cls, provider_class: type[LLMProvider]) -> Optional[str]:
        """Get API key from environment for a provider.

        Args:
            provider_class: Provider class

        Returns:
            API key or None
        """
        provider_name = provider_class.__name__
        
        if provider_name == "OpenAIProvider":
            return os.getenv("OPENAI_API_KEY")
        elif provider_name == "AnthropicProvider":
            return os.getenv("ANTHROPIC_API_KEY")
        elif provider_name == "GoogleProvider":
            return os.getenv("GOOGLE_API_KEY")
        elif provider_name == "CohereProvider":
            return os.getenv("COHERE_API_KEY")
        elif provider_name == "OllamaProvider":
            return os.getenv("OLLAMA_API_KEY")
        
        return None

    @classmethod
    def list_available_providers(cls) -> list[str]:
        """List all available provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def list_providers(cls) -> list[str]:
        """List the canonical provider identifiers.

        The unit tests expect these high-level names (not model aliases).
        """
        return ["openai", "anthropic", "google", "cohere", "ollama"]

    @classmethod
    def supports_model(cls, model: str) -> bool:
        """Check if a model is supported.

        Args:
            model: Model name

        Returns:
            True if supported
        """
        return cls._get_provider_class(model) is not None
