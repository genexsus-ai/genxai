import asyncio
import os

import pytest

from genxai.llm.factory import LLMProviderFactory

print("key: ",os.getenv("OPENAI_API_KEY"))
@pytest.mark.requires_api_key
def test_openai_llm_connection() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    provider = LLMProviderFactory.create_provider(
        model="gpt-4o",
        api_key=api_key,
        temperature=0.0,
        max_tokens=10,
    )

    async def _run() -> str:
        response = await provider.generate(
            prompt="Reply with the word: OK",
        )
        return response.content

    result = asyncio.run(_run())
    assert "OK" in result.upper()
