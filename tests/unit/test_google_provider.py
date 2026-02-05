"""Unit tests for Google Gemini provider."""

import sys
import warnings
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from genxai.llm.providers.google import GoogleProvider
from genxai.llm.base import LLMResponse


@pytest.fixture(autouse=True)
def mock_google_genai():
    """Mock Google Generative AI module."""
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
        yield mock_genai


def test_google_provider_init():
    """Test Google provider initialization."""
    provider = GoogleProvider(
        model="gemini-pro",
        api_key="test-key",
        temperature=0.8,
        max_tokens=1000,
    )
    
    assert provider.model == "gemini-pro"
    assert provider.api_key == "test-key"
    assert provider.temperature == 0.8
    assert provider.max_tokens == 1000
    provider.close()


def test_google_provider_init_with_env_var():
    """Test provider initialization with environment variable."""
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "env-test-key"}):
        provider = GoogleProvider(model="gemini-pro")
        assert provider.api_key == "env-test-key"
        provider.close()


def test_google_provider_init_no_api_key():
    """Test provider initialization without API key."""
    with patch.dict("os.environ", {}, clear=True):
        provider = GoogleProvider(model="gemini-ultra")
        assert provider.api_key is None
        provider.close()


@pytest.mark.asyncio
async def test_generate_success(mock_google_genai):
    """Test successful generation."""
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "Hello from Gemini!"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=10,
        candidates_token_count=5,
        total_token_count=15,
    )
    
    # Setup mock model
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    # Create provider and generate
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    result = await provider.generate(
        prompt="Hello",
        system_prompt="You are a helpful assistant",
    )
    
    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Gemini!"
    assert result.model == "gemini-pro"
    assert result.usage["prompt_tokens"] == 10
    assert result.usage["completion_tokens"] == 5
    assert result.usage["total_tokens"] == 15
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_without_system_prompt(mock_google_genai):
    """Test generation without system prompt."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=5,
        candidates_token_count=3,
        total_token_count=8,
    )
    
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    result = await provider.generate(prompt="Test")
    
    assert result.content == "Response"
    # Verify prompt was called without system prompt prepended
    call_args = mock_model.generate_content_async.call_args
    assert call_args[0][0] == "Test"
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_no_model():
    """Test generation without initialized model."""
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = None
    
    with pytest.raises(RuntimeError, match="Google Gemini client not initialized"):
        await provider.generate(prompt="Test")
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_stream(mock_google_genai):
    """Test streaming generation."""
    # Mock streaming response
    async def mock_stream_response():
        chunk1 = MagicMock()
        chunk1.text = "Hello "
        yield chunk1
        
        chunk2 = MagicMock()
        chunk2.text = "from "
        yield chunk2
        
        chunk3 = MagicMock()
        chunk3.text = "Gemini!"
        yield chunk3
    
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_stream_response())
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    chunks = []
    async for chunk in provider.generate_stream(prompt="Test"):
        chunks.append(chunk)
    
    assert chunks == ["Hello ", "from ", "Gemini!"]
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_chat(mock_google_genai):
    """Test chat generation."""
    mock_response = MagicMock()
    mock_response.text = "Chat response"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=20,
        candidates_token_count=10,
        total_token_count=30,
    )
    
    mock_chat = AsyncMock()
    mock_chat.send_message_async = AsyncMock(return_value=mock_response)
    
    mock_model = MagicMock()
    mock_model.start_chat = MagicMock(return_value=mock_chat)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]
    
    result = await provider.generate_chat(messages=messages)
    
    assert result.content == "Chat response"
    assert result.usage["total_tokens"] == 30
    await provider.aclose()


def test_provider_stats():
    """Test provider statistics tracking."""
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    
    # Initial stats
    stats = provider.get_stats()
    assert stats["total_tokens"] == 0
    assert stats["request_count"] == 0
    
    # Update stats
    provider._update_stats({"total_tokens": 100})
    provider._update_stats({"total_tokens": 50})
    
    stats = provider.get_stats()
    assert stats["total_tokens"] == 150
    assert stats["request_count"] == 2
    assert stats["avg_tokens_per_request"] == 75.0
    
    # Reset stats
    provider.reset_stats()
    stats = provider.get_stats()
    assert stats["total_tokens"] == 0
    assert stats["request_count"] == 0
    provider.close()


def test_provider_repr():
    """Test provider string representation."""
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    assert "GoogleProvider" in repr(provider)
    assert "gemini-pro" in repr(provider)
    provider.close()


@pytest.mark.asyncio
async def test_generate_with_additional_params(mock_google_genai):
    """Test generation with additional parameters."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=5,
        candidates_token_count=3,
        total_token_count=8,
    )
    
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    result = await provider.generate(
        prompt="Test",
        top_p=0.9,
        top_k=40,
        stop_sequences=["END"],
    )
    
    # Verify additional params were passed in generation_config
    call_args = mock_model.generate_content_async.call_args
    gen_config = call_args.kwargs["generation_config"]
    assert gen_config["top_p"] == 0.9
    assert gen_config["top_k"] == 40
    assert gen_config["stop_sequences"] == ["END"]
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_with_safety_settings(mock_google_genai):
    """Test generation with safety settings."""
    mock_response = MagicMock()
    mock_response.text = "Safe response"
    mock_response.candidates = [MagicMock(
        finish_reason="STOP",
        safety_ratings=[MagicMock(category="HARM_CATEGORY_HATE_SPEECH", probability="LOW")]
    )]
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=5,
        candidates_token_count=3,
        total_token_count=8,
    )
    
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ]
    
    result = await provider.generate(
        prompt="Test",
        safety_settings=safety_settings,
    )
    
    assert result.content == "Safe response"
    assert "safety_ratings" in result.metadata
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_api_error(mock_google_genai):
    """Test handling of API errors."""
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=Exception("API Error")
    )
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    with pytest.raises(Exception, match="API Error"):
        await provider.generate(prompt="Test")
    await provider.aclose()


@pytest.mark.asyncio
async def test_generate_without_usage_metadata(mock_google_genai):
    """Test generation when usage metadata is not available."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    mock_response.candidates = [MagicMock(finish_reason="STOP")]
    # No usage_metadata attribute
    delattr(mock_response, 'usage_metadata')
    
    mock_model = AsyncMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mock_google_genai.GenerativeModel.return_value = mock_model
    
    provider = GoogleProvider(model="gemini-pro", api_key="test-key")
    provider._model_instance = mock_model
    
    result = await provider.generate(prompt="Test")
    
    # Should default to 0 tokens
    assert result.usage["total_tokens"] == 0
    assert result.usage["prompt_tokens"] == 0
    assert result.usage["completion_tokens"] == 0
    await provider.aclose()
