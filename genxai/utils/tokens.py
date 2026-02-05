"""Token counting and context window management utilities."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# Model token limits (context window sizes)
MODEL_TOKEN_LIMITS: Dict[str, int] = {
    # OpenAI models
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-3.5-turbo": 4096,
    "gpt-3.5-turbo-16k": 16384,
    # Anthropic models
    "claude-3-opus": 200000,
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku": 200000,
    "claude-3-haiku-20240307": 200000,
    "claude-3-5-sonnet": 200000,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-5-sonnet-20240620": 200000,
    "claude-2.1": 200000,
    "claude-2": 100000,
    "claude-instant": 100000,
    # Google models
    "gemini-pro": 32768,
    "gemini-pro-vision": 16384,
    # Cohere models
    "command": 4096,
    "command-light": 4096,
    "command-nightly": 8192,
}


def get_model_token_limit(model: str) -> int:
    """Get token limit for a model.

    Args:
        model: Model name

    Returns:
        Token limit for the model, or 4096 as default
    """
    # Try exact match first
    if model in MODEL_TOKEN_LIMITS:
        return MODEL_TOKEN_LIMITS[model]
    
    # Try partial match (e.g., "gpt-4-0125-preview" matches "gpt-4")
    for model_prefix, limit in MODEL_TOKEN_LIMITS.items():
        if model.startswith(model_prefix):
            return limit
    
    # Default to conservative 4K limit
    logger.warning(f"Unknown model '{model}', using default 4096 token limit")
    return 4096


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    This is a simple estimation based on character count.
    For production use, consider using tiktoken library for accurate counting.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Rough estimation: ~4 characters per token for English text
    # This is conservative and works reasonably well for most cases
    return len(text) // 4


def truncate_to_token_limit(
    text: str,
    max_tokens: int,
    preserve_start: bool = True,
) -> str:
    """Truncate text to fit within token limit.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed
        preserve_start: If True, keep start of text; if False, keep end

    Returns:
        Truncated text
    """
    estimated_tokens = estimate_tokens(text)
    
    if estimated_tokens <= max_tokens:
        return text
    
    # Calculate how many characters to keep
    # Using 4 chars per token estimation
    max_chars = max_tokens * 4
    
    if preserve_start:
        truncated = text[:max_chars]
        logger.debug(f"Truncated text from {len(text)} to {len(truncated)} chars (start preserved)")
    else:
        truncated = text[-max_chars:]
        logger.debug(f"Truncated text from {len(text)} to {len(truncated)} chars (end preserved)")
    
    return truncated


def manage_context_window(
    system_prompt: str,
    user_prompt: str,
    memory_context: str,
    model: str,
    reserve_tokens: int = 1000,
) -> tuple[str, str, str]:
    """Manage context window to fit within model limits.

    Args:
        system_prompt: System prompt text
        user_prompt: User prompt text
        memory_context: Memory context text
        model: Model name
        reserve_tokens: Tokens to reserve for response

    Returns:
        Tuple of (system_prompt, user_prompt, memory_context) adjusted to fit
    """
    model_limit = get_model_token_limit(model)
    available_tokens = model_limit - reserve_tokens
    
    # Estimate current token usage
    system_tokens = estimate_tokens(system_prompt)
    user_tokens = estimate_tokens(user_prompt)
    memory_tokens = estimate_tokens(memory_context)
    total_tokens = system_tokens + user_tokens + memory_tokens
    
    logger.debug(
        f"Context window: {total_tokens}/{model_limit} tokens "
        f"(system: {system_tokens}, user: {user_tokens}, memory: {memory_tokens})"
    )
    
    # If within limit, return as-is
    if total_tokens <= available_tokens:
        return system_prompt, user_prompt, memory_context
    
    # Need to truncate - prioritize user prompt, then system, then memory
    tokens_to_remove = total_tokens - available_tokens
    
    logger.warning(
        f"Context window exceeded by {tokens_to_remove} tokens, truncating..."
    )
    
    # First, try truncating memory context
    if memory_tokens > 0 and tokens_to_remove > 0:
        memory_reduction = min(memory_tokens, tokens_to_remove)
        new_memory_tokens = max(0, memory_tokens - memory_reduction)
        memory_context = truncate_to_token_limit(
            memory_context,
            new_memory_tokens,
            preserve_start=False  # Keep most recent memories
        )
        tokens_to_remove -= memory_reduction
        logger.debug(f"Truncated memory context by {memory_reduction} tokens")
    
    # If still over limit, truncate system prompt
    if tokens_to_remove > 0 and system_tokens > 500:  # Keep at least 500 tokens
        system_reduction = min(system_tokens - 500, tokens_to_remove)
        new_system_tokens = max(500, system_tokens - system_reduction)
        system_prompt = truncate_to_token_limit(
            system_prompt,
            new_system_tokens,
            preserve_start=True  # Keep role/goal at start
        )
        tokens_to_remove -= system_reduction
        logger.debug(f"Truncated system prompt by {system_reduction} tokens")
    
    # If still over limit, truncate user prompt (last resort)
    if tokens_to_remove > 0 and user_tokens > 0:
        new_user_tokens = max(100, user_tokens - tokens_to_remove)  # Keep at least 100 tokens
        user_prompt = truncate_to_token_limit(
            user_prompt,
            new_user_tokens,
            preserve_start=True  # Keep task description
        )
        logger.warning(f"Had to truncate user prompt by {tokens_to_remove} tokens")
    
    return system_prompt, user_prompt, memory_context


def split_text_by_tokens(
    text: str,
    max_tokens_per_chunk: int,
    overlap_tokens: int = 100,
) -> List[str]:
    """Split text into chunks by token count.

    Args:
        text: Text to split
        max_tokens_per_chunk: Maximum tokens per chunk
        overlap_tokens: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    estimated_total_tokens = estimate_tokens(text)
    
    if estimated_total_tokens <= max_tokens_per_chunk:
        return [text]
    
    chunks = []
    chars_per_chunk = max_tokens_per_chunk * 4  # 4 chars per token
    overlap_chars = overlap_tokens * 4
    
    start = 0
    while start < len(text):
        end = start + chars_per_chunk
        chunk = text[start:end]
        chunks.append(chunk)
        
        # Move start forward, accounting for overlap
        start = end - overlap_chars
        
        if start >= len(text):
            break
    
    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks


class TokenCounter:
    """Token counter with caching for efficiency."""

    def __init__(self, model: str):
        """Initialize token counter.

        Args:
            model: Model name for token limit
        """
        self.model = model
        self.token_limit = get_model_token_limit(model)
        self._cache: Dict[str, int] = {}

    def count(self, text: str, use_cache: bool = True) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for
            use_cache: Whether to use cache

        Returns:
            Token count
        """
        if use_cache and text in self._cache:
            return self._cache[text]
        
        count = estimate_tokens(text)
        
        if use_cache:
            self._cache[text] = count
        
        return count

    def fits_in_context(
        self,
        *texts: str,
        reserve_tokens: int = 1000,
    ) -> bool:
        """Check if texts fit in context window.

        Args:
            *texts: Texts to check
            reserve_tokens: Tokens to reserve for response

        Returns:
            True if texts fit in context window
        """
        total_tokens = sum(self.count(text) for text in texts)
        available_tokens = self.token_limit - reserve_tokens
        return total_tokens <= available_tokens

    def clear_cache(self) -> None:
        """Clear token count cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, any]:
        """Get counter statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "model": self.model,
            "token_limit": self.token_limit,
            "cache_size": len(self._cache),
        }
