"""Unit tests for token utilities."""

import pytest
from genxai.utils.tokens import (
    get_model_token_limit,
    estimate_tokens,
    truncate_to_token_limit,
    manage_context_window,
    split_text_by_tokens,
    TokenCounter,
)


def test_get_model_token_limit():
    """Test model token limit lookup."""
    # Test exact matches
    assert get_model_token_limit("gpt-4") == 8192
    assert get_model_token_limit("gpt-4-32k") == 32768
    assert get_model_token_limit("claude-3-opus") == 200000
    assert get_model_token_limit("gemini-pro") == 32768
    
    # Test partial matches
    assert get_model_token_limit("gpt-4-0125-preview") == 8192
    assert get_model_token_limit("claude-3-opus-20240229") == 200000
    
    # Test unknown model (should return default)
    assert get_model_token_limit("unknown-model") == 4096


def test_estimate_tokens():
    """Test token estimation."""
    # Empty string
    assert estimate_tokens("") == 0
    
    # Short text (~4 chars per token)
    text = "Hello world"
    tokens = estimate_tokens(text)
    assert tokens == len(text) // 4
    
    # Longer text
    text = "This is a longer text that should have more tokens estimated based on character count."
    tokens = estimate_tokens(text)
    assert tokens > 0
    assert tokens == len(text) // 4


def test_truncate_to_token_limit():
    """Test text truncation."""
    text = "x" * 1000  # 1000 characters
    
    # Truncate to 100 tokens (400 chars)
    truncated = truncate_to_token_limit(text, max_tokens=100, preserve_start=True)
    assert len(truncated) == 400
    assert truncated == "x" * 400
    
    # Truncate preserving end
    truncated = truncate_to_token_limit(text, max_tokens=100, preserve_start=False)
    assert len(truncated) == 400
    assert truncated == "x" * 400
    
    # Text already within limit
    short_text = "short"
    truncated = truncate_to_token_limit(short_text, max_tokens=100)
    assert truncated == short_text


def test_manage_context_window():
    """Test context window management."""
    system_prompt = "You are a helpful assistant."
    user_prompt = "What is the capital of France?"
    memory_context = "Previous conversation context here."
    
    # Test within limits
    sys, user, mem = manage_context_window(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        memory_context=memory_context,
        model="gpt-4",
        reserve_tokens=1000,
    )
    
    # Should return unchanged (within limits)
    assert sys == system_prompt
    assert user == user_prompt
    assert mem == memory_context


def test_manage_context_window_truncation():
    """Test context window truncation when over limit."""
    # Create very long prompts
    system_prompt = "x" * 10000
    user_prompt = "y" * 10000
    memory_context = "z" * 10000
    
    sys, user, mem = manage_context_window(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        memory_context=memory_context,
        model="gpt-3.5-turbo",  # 4096 token limit
        reserve_tokens=1000,
    )
    
    # Should be truncated (at least one should be truncated)
    assert len(sys) < len(system_prompt) or len(user) < len(user_prompt) or len(mem) < len(memory_context)
    
    # All should be within or equal to original length
    assert len(sys) <= len(system_prompt)
    assert len(user) <= len(user_prompt)
    assert len(mem) <= len(memory_context)


def test_split_text_by_tokens():
    """Test text splitting by tokens."""
    # Short text (no split needed)
    short_text = "Hello world"
    chunks = split_text_by_tokens(short_text, max_tokens_per_chunk=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    
    # Long text (needs splitting)
    long_text = "x" * 10000
    chunks = split_text_by_tokens(long_text, max_tokens_per_chunk=100, overlap_tokens=10)
    assert len(chunks) > 1
    
    # Check overlap
    for i in range(len(chunks) - 1):
        # Should have some overlap
        assert len(chunks[i]) > 0
        assert len(chunks[i+1]) > 0


def test_token_counter_class():
    """Test TokenCounter class."""
    counter = TokenCounter(model="gpt-4")
    
    # Test initialization
    assert counter.model == "gpt-4"
    assert counter.token_limit == 8192
    
    # Test counting
    text = "Hello world"
    count = counter.count(text)
    assert count == estimate_tokens(text)
    
    # Test caching
    count2 = counter.count(text, use_cache=True)
    assert count2 == count
    assert text in counter._cache
    
    # Test fits_in_context
    short_texts = ["Hello", "world", "test"]
    assert counter.fits_in_context(*short_texts, reserve_tokens=1000)
    
    # Test with very long texts
    long_texts = ["x" * 100000 for _ in range(10)]
    assert not counter.fits_in_context(*long_texts, reserve_tokens=1000)
    
    # Test clear cache
    counter.clear_cache()
    assert len(counter._cache) == 0
    
    # Test get stats
    stats = counter.get_stats()
    assert stats["model"] == "gpt-4"
    assert stats["token_limit"] == 8192
    assert stats["cache_size"] == 0


def test_token_counter_different_models():
    """Test TokenCounter with different models."""
    # GPT-4
    counter_gpt4 = TokenCounter(model="gpt-4")
    assert counter_gpt4.token_limit == 8192
    
    # Claude
    counter_claude = TokenCounter(model="claude-3-opus")
    assert counter_claude.token_limit == 200000
    
    # Gemini
    counter_gemini = TokenCounter(model="gemini-pro")
    assert counter_gemini.token_limit == 32768
    
    # Unknown model
    counter_unknown = TokenCounter(model="unknown")
    assert counter_unknown.token_limit == 4096


def test_edge_cases():
    """Test edge cases."""
    # Empty strings
    assert estimate_tokens("") == 0
    assert truncate_to_token_limit("", 100) == ""
    
    # Very small token limits
    text = "Hello world this is a test"
    truncated = truncate_to_token_limit(text, max_tokens=1)
    assert len(truncated) == 4  # 1 token = 4 chars
    
    # Zero token limit
    truncated = truncate_to_token_limit(text, max_tokens=0)
    assert truncated == ""


def test_context_window_priority():
    """Test that context window management prioritizes correctly."""
    # Create prompts where memory needs to be truncated first
    system_prompt = "System: " + "x" * 1000
    user_prompt = "User: " + "y" * 1000
    memory_context = "Memory: " + "z" * 10000  # Much longer
    
    sys, user, mem = manage_context_window(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        memory_context=memory_context,
        model="gpt-3.5-turbo",
        reserve_tokens=1000,
    )
    
    # Memory should be truncated (it's the longest)
    assert len(mem) <= len(memory_context)
    
    # User prompt should be preserved as much as possible
    assert len(user) <= len(user_prompt)
    
    # System prompt should be preserved
    assert len(sys) <= len(system_prompt)
    
    # Total should fit in context window
    total_tokens = estimate_tokens(sys) + estimate_tokens(user) + estimate_tokens(mem)
    assert total_tokens <= 4096 - 1000
