"""Unit tests for Cohere provider."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from genxai.llm.providers.cohere import CohereProvider
from genxai.llm.base import LLMResponse


@pytest.fixture
def mock_cohere_client():
    """Mock Cohere client."""
    with patch("cohere.AsyncClient") as mock:
        yield mock


def test_cohere_provider_init():
    """Test Cohere provider initialization."""
    provider = CohereProvider(
        model="command",
        api_key="test-key",
        temperature=0.8,
        max_tokens=1000,
    )
    
    assert provider.model == "command"
    assert provider.api_key == "test-key"
    assert provider.temperature == 0.8
    assert provider.max_tokens == 1000
    provider.close()


def test_cohere_provider_init_with_env_var():
    """Test provider initialization with environment variable."""
    with patch.dict("os.environ", {"COHERE_API_KEY": "env-test-key"}):
        provider = CohereProvider(model="command-r")
        assert provider.api_key == "env-test-key"
        provider.close()


def test_cohere_provider_init_no_api_key():
    """Test provider initialization without API key."""
    with patch.dict("os.environ", {}, clear=True):
        provider = CohereProvider(model="command-light")
        assert provider.api_key is None
        provider.close()


@pytest.mark.asyncio
async def test_generate_success(mock_cohere_client):
    """Test successful generation."""
    # Mock response
    mock_generation = MagicMock()
    mock_generation.text = "Hello from Cohere!"
    mock_generation.finish_reason = "COMPLETE"
    mock_generation.id = "gen_123"
    
    mock_response = MagicMock()
    mock_response.generations = [mock_generation]
    mock_response.meta = MagicMock()
    mock_response.meta.billed_units = MagicMock(
        input_tokens=10,
        output_tokens=5,
    )
    
    # Setup mock client
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    # Create provider and generate
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(
        prompt="Hello",
        system_prompt="You are a helpful assistant",
    )
    
    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Cohere!"
    assert result.model == "command"
    assert result.usage["prompt_tokens"] == 10
    assert result.usage["completion_tokens"] == 5
    assert result.usage["total_tokens"] == 15
    assert result.finish_reason == "COMPLETE"
    provider.close()


@pytest.mark.asyncio
async def test_generate_without_system_prompt(mock_cohere_client):
    """Test generation without system prompt."""
    mock_generation = MagicMock()
    mock_generation.text = "Response"
    mock_generation.finish_reason = "COMPLETE"
    mock_generation.id = "gen_456"
    
    mock_response = MagicMock()
    mock_response.generations = [mock_generation]
    mock_response.meta = MagicMock()
    mock_response.meta.billed_units = MagicMock(input_tokens=5, output_tokens=3)
    
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(prompt="Test")
    
    assert result.content == "Response"
    # Verify prompt was called without system prompt prepended
    call_args = mock_client_instance.generate.call_args
    assert call_args.kwargs["prompt"] == "Test"
    provider.close()


@pytest.mark.asyncio
async def test_generate_no_client():
    """Test generation without initialized client."""
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = None
    
    with pytest.raises(RuntimeError, match="Cohere client not initialized"):
        await provider.generate(prompt="Test")
    provider.close()


@pytest.mark.asyncio
async def test_generate_stream(mock_cohere_client):
    """Test streaming generation."""
    # Mock streaming response
    async def mock_stream_response():
        event1 = MagicMock()
        event1.event_type = "text-generation"
        event1.text = "Hello "
        yield event1
        
        event2 = MagicMock()
        event2.event_type = "text-generation"
        event2.text = "from "
        yield event2
        
        event3 = MagicMock()
        event3.event_type = "text-generation"
        event3.text = "Cohere!"
        yield event3
    
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(return_value=mock_stream_response())
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    chunks = []
    async for chunk in provider.generate_stream(prompt="Test"):
        chunks.append(chunk)
    
    assert chunks == ["Hello ", "from ", "Cohere!"]
    provider.close()


@pytest.mark.asyncio
async def test_generate_chat(mock_cohere_client):
    """Test chat generation."""
    mock_response = MagicMock()
    mock_response.text = "Chat response"
    mock_response.finish_reason = "COMPLETE"
    mock_response.generation_id = "gen_789"
    mock_response.meta = MagicMock()
    mock_response.meta.billed_units = MagicMock(input_tokens=20, output_tokens=10)
    
    mock_client_instance = AsyncMock()
    mock_client_instance.chat = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]
    
    result = await provider.generate_chat(messages=messages)
    
    assert result.content == "Chat response"
    assert result.usage["total_tokens"] == 30
    
    # Verify chat history was passed correctly
    call_args = mock_client_instance.chat.call_args
    assert "chat_history" in call_args.kwargs
    assert "preamble" in call_args.kwargs  # System prompt as preamble
    provider.close()


def test_provider_stats():
    """Test provider statistics tracking."""
    provider = CohereProvider(model="command", api_key="test-key")
    
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
    provider = CohereProvider(model="command", api_key="test-key")
    assert "CohereProvider" in repr(provider)
    assert "command" in repr(provider)
    provider.close()


@pytest.mark.asyncio
async def test_generate_with_additional_params(mock_cohere_client):
    """Test generation with additional parameters."""
    mock_generation = MagicMock()
    mock_generation.text = "Response"
    mock_generation.finish_reason = "COMPLETE"
    mock_generation.id = "gen_999"
    
    mock_response = MagicMock()
    mock_response.generations = [mock_generation]
    mock_response.meta = MagicMock()
    mock_response.meta.billed_units = MagicMock(input_tokens=5, output_tokens=3)
    
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(
        prompt="Test",
        p=0.9,
        k=40,
        frequency_penalty=0.5,
        presence_penalty=0.3,
        stop_sequences=["END"],
    )
    
    # Verify additional params were passed
    call_args = mock_client_instance.generate.call_args
    assert call_args.kwargs["p"] == 0.9
    assert call_args.kwargs["k"] == 40
    assert call_args.kwargs["frequency_penalty"] == 0.5
    assert call_args.kwargs["presence_penalty"] == 0.3
    assert call_args.kwargs["stop_sequences"] == ["END"]
    provider.close()


@pytest.mark.asyncio
async def test_generate_api_error(mock_cohere_client):
    """Test handling of API errors."""
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(
        side_effect=Exception("API Error")
    )
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    with pytest.raises(Exception, match="API Error"):
        await provider.generate(prompt="Test")
    provider.close()


@pytest.mark.asyncio
async def test_generate_without_usage_metadata(mock_cohere_client):
    """Test generation when usage metadata is not available."""
    mock_generation = MagicMock()
    mock_generation.text = "Response"
    mock_generation.finish_reason = "COMPLETE"
    mock_generation.id = "gen_000"
    
    mock_response = MagicMock()
    mock_response.generations = [mock_generation]
    mock_response.meta = None  # No meta
    
    mock_client_instance = AsyncMock()
    mock_client_instance.generate = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(prompt="Test")
    
    # Should default to 0 tokens
    assert result.usage["total_tokens"] == 0
    assert result.usage["prompt_tokens"] == 0
    assert result.usage["completion_tokens"] == 0
    provider.close()


@pytest.mark.asyncio
async def test_chat_with_empty_history(mock_cohere_client):
    """Test chat generation with only one message."""
    mock_response = MagicMock()
    mock_response.text = "Response"
    mock_response.finish_reason = "COMPLETE"
    mock_response.generation_id = "gen_111"
    mock_response.meta = MagicMock()
    mock_response.meta.billed_units = MagicMock(input_tokens=5, output_tokens=3)
    
    mock_client_instance = AsyncMock()
    mock_client_instance.chat = AsyncMock(return_value=mock_response)
    mock_cohere_client.AsyncClient.return_value = mock_client_instance
    
    provider = CohereProvider(model="command", api_key="test-key")
    provider._client = mock_client_instance
    
    messages = [
        {"role": "user", "content": "Hello"},
    ]
    
    result = await provider.generate_chat(messages=messages)
    
    assert result.content == "Response"
    
    # Verify no chat_history was passed (empty history)
    call_args = mock_client_instance.chat.call_args
    assert "chat_history" not in call_args.kwargs or not call_args.kwargs.get("chat_history")
    provider.close()
