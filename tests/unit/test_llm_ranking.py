"""Unit tests for the LLM ranking utility."""

import pytest

from genxai.utils.llm_ranking import RankCandidate, rank_candidates_with_llm
from tests.utils.mock_llm import MockLLMProvider


@pytest.mark.asyncio
async def test_rank_candidates_with_llm_valid_json() -> None:
    provider = MockLLMProvider(
        response_text=(
            "{"
            "\"ranked_ids\":[\"a\",\"b\"],"
            "\"scores\":{\"a\":0.9,\"b\":0.1},"
            "\"rationales\":{\"a\":\"best\",\"b\":\"ok\"},"
            "\"selected_id\":\"a\","
            "\"confidence\":0.82"
            "}"
        ),
    )
    decision = await rank_candidates_with_llm(
        task="Pick best",
        candidates=[
            RankCandidate(id="a", content="Alpha"),
            RankCandidate(id="b", content="Beta"),
        ],
        llm_provider=provider,
    )

    assert decision.selected_id == "a"
    assert decision.ranked_ids[0] == "a"
    assert decision.method_used == "llm"
    assert decision.scores["a"] >= decision.scores["b"]


@pytest.mark.asyncio
async def test_rank_candidates_with_llm_repaired_json() -> None:
    provider = MockLLMProvider(
        response_text=(
            "Here is your JSON: {'ranked_ids': ['b', 'a'], 'scores': {'a': 0.2, 'b': 0.8}, "
            "'rationales': {'a': 'ok', 'b': 'best'}, 'selected_id': 'b', 'confidence': 0.6}"
        ),
    )

    decision = await rank_candidates_with_llm(
        task="Pick best",
        candidates=[
            RankCandidate(id="a", content="Alpha"),
            RankCandidate(id="b", content="Beta"),
        ],
        llm_provider=provider,
    )

    assert decision.selected_id == "b"
    assert decision.ranked_ids[0] == "b"
    assert decision.method_used in {"llm", "repaired_llm"}


@pytest.mark.asyncio
async def test_rank_candidates_with_llm_fallback() -> None:
    provider = MockLLMProvider(response_text="No JSON here.")
    decision = await rank_candidates_with_llm(
        task="Find alpha",
        candidates=[
            RankCandidate(id="a", content="Alpha response"),
            RankCandidate(id="b", content="Beta response"),
        ],
        llm_provider=provider,
    )

    assert decision.method_used == "heuristic_fallback"
    assert decision.selected_id in {"a", "b"}


@pytest.mark.asyncio
async def test_rank_candidates_with_llm_fallback_keywords_and_phrase() -> None:
    provider = MockLLMProvider(response_text="N/A")
    decision = await rank_candidates_with_llm(
        task="exact phrase",
        candidates=[
            RankCandidate(
                id="a",
                content="This includes the exact phrase in content.",
                metadata={"keywords": ["exact", "phrase", "other"]},
            ),
            RankCandidate(
                id="b",
                content="No match here.",
                metadata={"keywords": ["unrelated"]},
            ),
        ],
        llm_provider=provider,
    )

    assert decision.method_used == "heuristic_fallback"
    assert decision.selected_id == "a"