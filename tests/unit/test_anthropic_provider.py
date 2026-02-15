"""Unit tests for Anthropic Claude provider."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from genxai.llm.providers.anthropic import AnthropicProvider
from genxai.llm.base import LLMResponse

# These provider tests require the optional `anthropic` SDK.
# Skip the entire module cleanly when it isn't installed (common in minimal/dev installs).
pytest.importorskip("anthropic")


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    with patch("anthropic.AsyncAnthropic") as mock:
        yield mock


def test_anthropic_provider_init():
    """Test Anthropic provider initialization."""
    provider = AnthropicProvider(
        model="claude-3-opus-20240229",
        api_key="test-key",
        temperature=0.8,
        max_tokens=1000,
    )
    
    assert provider.model == "claude-3-opus-20240229"
    assert provider.api_key == "test-key"
    assert provider.temperature == 0.8
    assert provider.max_tokens == 1000
    provider.close()


def test_anthropic_provider_init_with_env_var():
    """Test provider initialization with environment variable."""
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-test-key"}):
        provider = AnthropicProvider(model="claude-3-sonnet-20240229")
        assert provider.api_key == "env-test-key"
        provider.close()


def test_anthropic_provider_init_no_api_key():
    """Test provider initialization without API key."""
    with patch.dict("os.environ", {}, clear=True):
        provider = AnthropicProvider(model="claude-3-haiku-20240229")
        assert provider.api_key is None
        provider.close()


@pytest.mark.asyncio
async def test_generate_success(mock_anthropic_client):
    """Test successful generation."""
    # Mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello from Claude!")]
    mock_response.model = "claude-3-opus-20240229"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = MagicMock(
        input_tokens=10,
        output_tokens=5,
    )
    mock_response.id = "msg_123"
    mock_response.type = "message"
    
    # Setup mock client
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic_client.return_value = mock_client_instance
    
    # Create provider and generate
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(
        prompt="Hello",
        system_prompt="You are a helpful assistant",
    )
    
    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Claude!"
    assert result.model == "claude-3-opus-20240229"
    assert result.usage["prompt_tokens"] == 10
    assert result.usage["completion_tokens"] == 5
    assert result.usage["total_tokens"] == 15
    assert result.finish_reason == "end_turn"
    provider.close()


@pytest.mark.asyncio
async def test_generate_without_system_prompt(mock_anthropic_client):
    """Test generation without system prompt."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_response.model = "claude-3-sonnet-20240229"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = MagicMock(input_tokens=5, output_tokens=3)
    mock_response.id = "msg_456"
    mock_response.type = "message"
    
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic_client.return_value = mock_client_instance
    
    provider = AnthropicProvider(model="claude-3-sonnet-20240229", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(prompt="Test")
    
    assert result.content == "Response"
    # Verify system prompt was not included in call
    call_args = mock_client_instance.messages.create.call_args
    assert "system" not in call_args.kwargs
    provider.close()


@pytest.mark.asyncio
async def test_generate_no_client():
    """Test generation without initialized client."""
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    provider._client = None
    
    with pytest.raises(RuntimeError, match="Anthropic client not initialized"):
        await provider.generate(prompt="Test")
    provider.close()


@pytest.mark.asyncio
async def test_generate_stream(mock_anthropic_client):
    """Test streaming generation."""
    # Mock streaming response
    async def mock_text_stream():
        yield "Hello "
        yield "from "
        yield "Claude!"
    
    mock_stream = MagicMock()
    mock_stream.text_stream = mock_text_stream()
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=None)
    
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.stream = MagicMock(return_value=mock_stream)
    mock_anthropic_client.return_value = mock_client_instance
    
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    provider._client = mock_client_instance
    
    chunks = []
    async for chunk in provider.generate_stream(prompt="Test"):
        chunks.append(chunk)
    
    assert chunks == ["Hello ", "from ", "Claude!"]
    provider.close()


@pytest.mark.asyncio
async def test_generate_chat(mock_anthropic_client):
    """Test chat generation."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Chat response")]
    mock_response.model = "claude-3-opus-20240229"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = MagicMock(input_tokens=20, output_tokens=10)
    mock_response.id = "msg_789"
    mock_response.type = "message"
    
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic_client.return_value = mock_client_instance
    
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
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
    provider.close()


def test_provider_stats():
    """Test provider statistics tracking."""
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    
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
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    assert "AnthropicProvider" in repr(provider)
    assert "claude-3-opus-20240229" in repr(provider)
    provider.close()


@pytest.mark.asyncio
async def test_generate_with_additional_params(mock_anthropic_client):
    """Test generation with additional parameters."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Response")]
    mock_response.model = "claude-3-opus-20240229"
    mock_response.stop_reason = "end_turn"
    mock_response.usage = MagicMock(input_tokens=5, output_tokens=3)
    mock_response.id = "msg_999"
    mock_response.type = "message"
    
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic_client.return_value = mock_client_instance
    
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    provider._client = mock_client_instance
    
    result = await provider.generate(
        prompt="Test",
        top_p=0.9,
        top_k=40,
        stop_sequences=["END"],
    )
    
    # Verify additional params were passed
    call_args = mock_client_instance.messages.create.call_args
    assert call_args.kwargs["top_p"] == 0.9
    assert call_args.kwargs["top_k"] == 40
    assert call_args.kwargs["stop_sequences"] == ["END"]
    provider.close()


@pytest.mark.asyncio
async def test_generate_api_error(mock_anthropic_client):
    """Test handling of API errors."""
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(
        side_effect=Exception("API Error")
    )
    mock_anthropic_client.return_value = mock_client_instance
    
    provider = AnthropicProvider(model="claude-3-opus-20240229", api_key="test-key")
    provider._client = mock_client_instance
    
    with pytest.raises(Exception, match="API Error"):
        await provider.generate(prompt="Test")
    provider.close()
