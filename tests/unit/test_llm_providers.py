"""Enhanced tests for LLM providers."""

import sys
import pytest
import os
from unittest.mock import MagicMock, patch
from genxai.llm.factory import LLMProviderFactory
from genxai.llm.providers.openai import OpenAIProvider
from genxai.llm.providers.anthropic import AnthropicProvider
from genxai.llm.providers.google import GoogleProvider
from genxai.llm.providers.cohere import CohereProvider
from genxai.llm.providers.ollama import OllamaProvider


# ==================== LLM Factory Tests ====================


@pytest.fixture(autouse=True)
def mock_google_genai():
    """Stub google genai modules to avoid importing deprecated packages."""
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = MagicMock()
    mock_google = MagicMock()
    mock_google.genai = mock_genai
    with patch.dict(
        sys.modules,
        {
            "google": mock_google,
            "google.genai": mock_genai,
            "google.generativeai": mock_genai,
        },
    ):
        yield

def test_llm_factory_create_openai():
    """Test creating OpenAI provider."""
    provider = LLMProviderFactory.create_provider("openai", api_key="test_key")
    assert provider is not None
    assert isinstance(provider, OpenAIProvider)
    provider.close()


def test_llm_factory_create_anthropic():
    """Test creating Anthropic provider."""
    provider = LLMProviderFactory.create_provider("anthropic", api_key="test_key")
    assert provider is not None
    assert isinstance(provider, AnthropicProvider)
    provider.close()


def test_llm_factory_create_google():
    """Test creating Google provider."""
    provider = LLMProviderFactory.create_provider("google", api_key="test_key")
    assert provider is not None
    assert isinstance(provider, GoogleProvider)
    provider.close()


def test_llm_factory_create_cohere():
    """Test creating Cohere provider."""
    provider = LLMProviderFactory.create_provider("cohere", api_key="test_key")
    assert provider is not None
    assert isinstance(provider, CohereProvider)
    provider.close()


def test_llm_factory_invalid_provider():
    """Test creating invalid provider."""
    with pytest.raises(ValueError):
        LLMProviderFactory.create_provider("invalid_provider", api_key="test")


def test_llm_factory_list_providers():
    """Test listing available providers."""
    providers = LLMProviderFactory.list_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "google" in providers
    assert "cohere" in providers
    assert "ollama" in providers


# ==================== OpenAI Provider Tests ====================

def test_openai_provider_initialization():
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider(api_key="test_key")
    assert provider.api_key == "test_key"
    assert provider.model is not None
    provider.close()


def test_openai_provider_with_model():
    """Test OpenAI provider with specific model."""
    provider = OpenAIProvider(api_key="test_key", model="gpt-4")
    assert provider.model == "gpt-4"
    provider.close()


def test_openai_provider_with_temperature():
    """Test OpenAI provider with temperature."""
    provider = OpenAIProvider(api_key="test_key", temperature=0.5)
    assert provider.temperature == 0.5
    provider.close()


def test_openai_provider_missing_api_key():
    """Test OpenAI provider without API key."""
    with pytest.raises((ValueError, TypeError)):
        OpenAIProvider()


# ==================== Anthropic Provider Tests ====================

def test_anthropic_provider_initialization():
    """Test Anthropic provider initialization."""
    provider = AnthropicProvider(api_key="test_key")
    assert provider.api_key == "test_key"
    provider.close()


def test_anthropic_provider_with_model():
    """Test Anthropic provider with specific model."""
    provider = AnthropicProvider(api_key="test_key", model="claude-3-opus")
    assert provider.requested_model == "claude-3-opus"
    provider.close()


def test_anthropic_provider_with_max_tokens():
    """Test Anthropic provider with max tokens."""
    provider = AnthropicProvider(api_key="test_key", max_tokens=2000)
    assert provider.max_tokens == 2000
    provider.close()


# ==================== Google Provider Tests ====================

def test_google_provider_initialization():
    """Test Google provider initialization."""
    provider = GoogleProvider(api_key="test_key")
    assert provider.api_key == "test_key"
    provider.close()


def test_google_provider_with_model():
    """Test Google provider with specific model."""
    provider = GoogleProvider(api_key="test_key", model="gemini-pro")
    assert provider.model == "gemini-pro"
    provider.close()


# ==================== Cohere Provider Tests ====================

def test_cohere_provider_initialization():
    """Test Cohere provider initialization."""
    provider = CohereProvider(api_key="test_key")
    assert provider.api_key == "test_key"
    provider.close()


def test_cohere_provider_with_model():
    """Test Cohere provider with specific model."""
    provider = CohereProvider(api_key="test_key", model="command")
    assert provider.model == "command"
    provider.close()


# ==================== Provider Comparison Tests ====================

def test_all_providers_have_generate_method():
    """Test that all providers have generate method."""
    providers = [
        OpenAIProvider(api_key="test"),
        AnthropicProvider(api_key="test"),
        GoogleProvider(api_key="test"),
        CohereProvider(api_key="test"),
        OllamaProvider()
    ]
    
    for provider in providers:
        assert hasattr(provider, "generate")
        if hasattr(provider, "close"):
            provider.close()


def test_all_providers_have_api_key():
    """Test that all providers store API key."""
    providers = [
        OpenAIProvider(api_key="test_key"),
        AnthropicProvider(api_key="test_key"),
        GoogleProvider(api_key="test_key"),
        CohereProvider(api_key="test_key"),
        OllamaProvider(api_key="test_key")
    ]
    
    for provider in providers:
        assert provider.api_key == "test_key"
        if hasattr(provider, "close"):
            provider.close()


def test_all_providers_have_model():
    """Test that all providers have model attribute."""
    providers = [
        OpenAIProvider(api_key="test"),
        AnthropicProvider(api_key="test"),
        GoogleProvider(api_key="test"),
        CohereProvider(api_key="test"),
        OllamaProvider()
    ]
    
    for provider in providers:
        assert hasattr(provider, "model")
        assert provider.model is not None
        if hasattr(provider, "close"):
            provider.close()
