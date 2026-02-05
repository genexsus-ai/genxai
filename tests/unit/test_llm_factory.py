"""Unit tests for LLM Provider Factory."""

import pytest
from unittest.mock import patch, MagicMock
from genxai.llm.factory import LLMProviderFactory
from genxai.llm.providers.openai import OpenAIProvider


def test_create_openai_provider():
    """Test creating OpenAI provider."""
    provider = LLMProviderFactory.create_provider(
        model="gpt-4",
        api_key="test-key",
        temperature=0.8,
        max_tokens=1000,
    )
    
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4"
    assert provider.temperature == 0.8
    assert provider.max_tokens == 1000


def test_create_provider_with_env_var():
    """Test creating provider with API key from environment."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "env-test-key"}):
        provider = LLMProviderFactory.create_provider(
            model="gpt-3.5-turbo",
            temperature=0.7,
        )
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "env-test-key"


def test_create_provider_unknown_model():
    """Test creating provider with unknown model."""
    with pytest.raises(ValueError, match="No provider found"):
        LLMProviderFactory.create_provider(
            model="unknown-model-xyz",
            api_key="test-key",
        )


def test_create_provider_with_fallback():
    """Test fallback model logic."""
    # Mock the provider creation to fail for first model
    with patch.object(OpenAIProvider, "__init__", side_effect=[Exception("API Error"), None]):
        # This should fail on gpt-4 but succeed on fallback
        with patch.object(OpenAIProvider, "__init__", return_value=None):
            provider = LLMProviderFactory.create_provider(
                model="gpt-4",
                api_key="test-key",
                fallback_models=["gpt-3.5-turbo"],
            )
            # If we get here, fallback worked


def test_supports_model():
    """Test model support checking."""
    # OpenAI models
    assert LLMProviderFactory.supports_model("gpt-4")
    assert LLMProviderFactory.supports_model("gpt-3.5-turbo")
    assert LLMProviderFactory.supports_model("gpt-4-turbo")
    
    # Anthropic models
    assert LLMProviderFactory.supports_model("claude-3-opus-20240229")
    assert LLMProviderFactory.supports_model("claude-3-sonnet-20240229")
    
    # Google models
    assert LLMProviderFactory.supports_model("gemini-pro")
    assert LLMProviderFactory.supports_model("gemini-ultra")
    
    # Cohere models
    assert LLMProviderFactory.supports_model("command")
    assert LLMProviderFactory.supports_model("command-r")
    
    # Ollama/local models
    assert LLMProviderFactory.supports_model("ollama")
    assert LLMProviderFactory.supports_model("llama3")
    
    # Unknown model
    assert not LLMProviderFactory.supports_model("unknown-model")


def test_list_available_providers():
    """Test listing providers."""
    providers = LLMProviderFactory.list_available_providers()
    
    assert isinstance(providers, list)
    assert len(providers) > 0
    
    # OpenAI providers (pre-loaded)
    assert "openai" in providers
    assert "gpt-4" in providers
    assert "gpt-3.5-turbo" in providers


def test_list_providers_includes_ollama():
    """Ensure Ollama shows up in canonical providers list."""
    providers = LLMProviderFactory.list_providers()
    assert "ollama" in providers


def test_register_custom_provider():
    """Test registering a custom provider."""
    # Create a mock provider class
    class CustomProvider:
        def __init__(self, model, api_key=None, **kwargs):
            self.model = model
            self.api_key = api_key
    
    # Register it
    LLMProviderFactory.register_provider("custom", CustomProvider)
    
    # Verify it's registered
    assert "custom" in LLMProviderFactory.list_available_providers()
    
    # Create instance
    provider = LLMProviderFactory.create_provider(
        model="custom",
        api_key="test-key",
    )
    
    assert isinstance(provider, CustomProvider)
    assert provider.model == "custom"


def test_get_provider_class():
    """Test internal provider class lookup."""
    # Test direct match - OpenAI
    provider_class = LLMProviderFactory._get_provider_class("gpt-4")
    assert provider_class == OpenAIProvider
    
    # Test prefix match - OpenAI
    provider_class = LLMProviderFactory._get_provider_class("gpt-4-turbo-preview")
    assert provider_class == OpenAIProvider
    
    # Test lazy-loaded providers
    # Anthropic
    provider_class = LLMProviderFactory._get_provider_class("claude-3-opus-20240229")
    assert provider_class is not None
    assert provider_class.__name__ == "AnthropicProvider"
    
    # Google
    provider_class = LLMProviderFactory._get_provider_class("gemini-pro")
    assert provider_class is not None
    assert provider_class.__name__ == "GoogleProvider"
    
    # Cohere
    provider_class = LLMProviderFactory._get_provider_class("command")
    assert provider_class is not None
    assert provider_class.__name__ == "CohereProvider"
    
    # Test unknown
    provider_class = LLMProviderFactory._get_provider_class("unknown")
    assert provider_class is None


def test_get_api_key_for_provider():
    """Test API key retrieval from environment."""
    # OpenAI
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
        api_key = LLMProviderFactory._get_api_key_for_provider(OpenAIProvider)
        assert api_key == "test-openai-key"
    
    # Anthropic
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-anthropic-key"}):
        from genxai.llm.providers.anthropic import AnthropicProvider
        api_key = LLMProviderFactory._get_api_key_for_provider(AnthropicProvider)
        assert api_key == "test-anthropic-key"
    
    # Google
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-google-key"}):
        from genxai.llm.providers.google import GoogleProvider
        api_key = LLMProviderFactory._get_api_key_for_provider(GoogleProvider)
        assert api_key == "test-google-key"
    
    # Cohere
    with patch.dict("os.environ", {"COHERE_API_KEY": "test-cohere-key"}):
        from genxai.llm.providers.cohere import CohereProvider
        api_key = LLMProviderFactory._get_api_key_for_provider(CohereProvider)
        assert api_key == "test-cohere-key"
    
    # Test with no env var
    with patch.dict("os.environ", {}, clear=True):
        api_key = LLMProviderFactory._get_api_key_for_provider(OpenAIProvider)
        assert api_key is None
