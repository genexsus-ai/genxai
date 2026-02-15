"""LLM-based ranking utility with safe JSON parsing and heuristic fallback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import json
import logging
import math
import re

from genxai.llm.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RankCandidate:
    """Candidate to be ranked by the LLM utility."""

    id: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RankDecision:
    """Decision payload from the ranking utility."""

    selected_id: str
    ranked_ids: List[str]
    scores: Dict[str, float]
    rationales: Dict[str, str]
    confidence: float
    method_used: str
    raw_response: Optional[str] = None


DEFAULT_RANKING_SYSTEM_PROMPT = (
    "You are an expert evaluator. Rank the provided candidates strictly by how well they satisfy the task. "
    "You must output a JSON object only, no markdown or extra commentary."
)


def _build_ranking_prompt(
    task: str,
    candidates: Iterable[RankCandidate],
    criteria: Optional[Iterable[str]] = None,
    weights: Optional[Mapping[str, float]] = None,
) -> str:
    """Build a clear user prompt with explicit JSON schema requirements."""

    criteria_list = list(criteria or [])
    weight_map = dict(weights or {})

    criteria_block = ""
    if criteria_list:
        criteria_block = (
            "\nCriteria (higher is better):\n"
            + "\n".join(f"- {item}" for item in criteria_list)
        )

    weights_block = ""
    if weight_map:
        weights_block = (
            "\nWeights (optional guidance):\n"
            + "\n".join(f"- {key}: {value}" for key, value in weight_map.items())
        )

    candidates_block = "\n".join(
        [
            f"ID: {cand.id}\nCONTENT: {cand.content}\nMETADATA: {dict(cand.metadata)}"
            for cand in candidates
        ]
    )

    return (
        f"Task: {task}\n"
        f"You must rank the candidates and respond ONLY with JSON using this schema:\n"
        "{\n"
        "  \"ranked_ids\": [\"id1\", \"id2\"],\n"
        "  \"scores\": {\"id1\": 0.9, \"id2\": 0.1},\n"
        "  \"rationales\": {\"id1\": \"...\", \"id2\": \"...\"},\n"
        "  \"selected_id\": \"id1\",\n"
        "  \"confidence\": 0.85\n"
        "}\n"
        f"Candidates:\n{candidates_block}"
        f"{criteria_block}"
        f"{weights_block}"
    )


def _clamp_score(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def _normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    clamped = {key: _clamp_score(val) for key, val in scores.items()}
    max_score = max(clamped.values()) if clamped else 0.0
    if max_score <= 0:
        return clamped
    return {key: val / max_score for key, val in clamped.items()}


def _extract_json_block(text: str) -> Optional[str]:
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def _safe_parse_ranking_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        extracted = _extract_json_block(text)
        if extracted:
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                repaired_extracted = extracted.replace("'", '"')
                try:
                    return json.loads(repaired_extracted)
                except json.JSONDecodeError:
                    pass

        repaired = text.replace("'", '"')
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            return None


def _validate_and_normalize_decision(
    payload: Dict[str, Any],
    candidates: List[RankCandidate],
) -> Optional[Tuple[List[str], Dict[str, float], Dict[str, str], str, float]]:
    candidate_ids = {cand.id for cand in candidates}

    ranked_ids_raw = payload.get("ranked_ids", [])
    if not isinstance(ranked_ids_raw, list):
        return None
    ranked_ids = [rid for rid in ranked_ids_raw if isinstance(rid, str) and rid in candidate_ids]

    scores_raw = payload.get("scores", {})
    if not isinstance(scores_raw, dict):
        return None
    scores = {
        cid: float(scores_raw.get(cid, 0.0))
        for cid in candidate_ids
        if isinstance(scores_raw.get(cid, 0.0), (int, float))
    }

    scores = _normalize_scores(scores)
    missing = [cid for cid in candidate_ids if cid not in ranked_ids]
    ranked_ids.extend(sorted(missing, key=lambda cid: scores.get(cid, 0.0), reverse=True))

    rationales_raw = payload.get("rationales", {})
    rationales = {
        cid: str(rationales_raw.get(cid, ""))
        for cid in candidate_ids
        if isinstance(rationales_raw, dict)
    }

    selected_id = payload.get("selected_id")
    if selected_id not in candidate_ids:
        selected_id = ranked_ids[0] if ranked_ids else candidates[0].id

    confidence = payload.get("confidence", 0.0)
    try:
        confidence_val = _clamp_score(float(confidence))
    except (TypeError, ValueError):
        confidence_val = 0.0

    if ranked_ids and ranked_ids[0] != selected_id:
        ranked_ids = [selected_id] + [cid for cid in ranked_ids if cid != selected_id]

    return ranked_ids, scores, rationales, selected_id, confidence_val


def _token_overlap_score(task: str, content: str) -> float:
    task_tokens = set(re.findall(r"\w+", task.lower()))
    content_tokens = set(re.findall(r"\w+", content.lower()))
    if not task_tokens or not content_tokens:
        return 0.0
    overlap = len(task_tokens & content_tokens)
    return overlap / max(1, len(task_tokens))


def _keyword_match_score(task: str, metadata: Mapping[str, Any]) -> float:
    """Score based on keyword/tag matches in metadata."""
    if not metadata:
        return 0.0
    keywords = metadata.get("keywords") or metadata.get("tags") or []
    if not isinstance(keywords, (list, tuple, set)):
        return 0.0
    task_tokens = set(re.findall(r"\w+", task.lower()))
    keyword_tokens = {str(item).lower() for item in keywords}
    if not task_tokens or not keyword_tokens:
        return 0.0
    overlap = len(task_tokens & keyword_tokens)
    return overlap / max(1, len(keyword_tokens))


def _phrase_match_score(task: str, content: str) -> float:
    """Boost when exact phrases from the task appear in candidate content."""
    task_phrase = task.strip().lower()
    if not task_phrase or not content:
        return 0.0
    return 1.0 if task_phrase in content.lower() else 0.0


def _heuristic_fallback_rank(
    task: str,
    candidates: List[RankCandidate],
    weights: Optional[Mapping[str, float]] = None,
) -> Tuple[List[str], Dict[str, float], Dict[str, str], str, float]:
    weights = dict(weights or {})
    length_weight = float(weights.get("length", 0.25))
    overlap_weight = float(weights.get("overlap", 0.55))
    meta_weight = float(weights.get("metadata", 0.1))
    keyword_weight = float(weights.get("keywords", 0.2))
    phrase_weight = float(weights.get("phrase", 0.15))

    scores: Dict[str, float] = {}
    rationales: Dict[str, str] = {}
    for cand in candidates:
        overlap = _token_overlap_score(task, cand.content)
        length_score = min(1.0, len(cand.content) / 800) if cand.content else 0.0
        meta_boost = 0.0
        if cand.metadata:
            meta_boost = sum(1 for value in cand.metadata.values() if value) / max(1, len(cand.metadata))
        keyword_score = _keyword_match_score(task, cand.metadata)
        phrase_score = _phrase_match_score(task, cand.content)
        score = (
            overlap_weight * overlap
            + length_weight * length_score
            + meta_weight * meta_boost
            + keyword_weight * keyword_score
            + phrase_weight * phrase_score
        )
        scores[cand.id] = _clamp_score(score)
        rationales[cand.id] = (
            "heuristic: "
            f"overlap={overlap:.2f}, length={length_score:.2f}, metadata={meta_boost:.2f}, "
            f"keywords={keyword_score:.2f}, phrase={phrase_score:.2f}"
        )

    scores = _normalize_scores(scores)
    ranked_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    selected_id = ranked_ids[0] if ranked_ids else candidates[0].id
    confidence = min(0.7, scores.get(selected_id, 0.0) + 0.1)
    return ranked_ids, scores, rationales, selected_id, confidence


async def rank_candidates_with_llm(
    *,
    task: str,
    candidates: Iterable[RankCandidate],
    llm_provider: LLMProvider,
    system_prompt: str = DEFAULT_RANKING_SYSTEM_PROMPT,
    criteria: Optional[Iterable[str]] = None,
    weights: Optional[Mapping[str, float]] = None,
) -> RankDecision:
    """Rank candidates with the LLM and fallback heuristics if parsing fails."""

    candidates_list = list(candidates)
    if not candidates_list:
        raise ValueError("At least one candidate is required for ranking")

    prompt = _build_ranking_prompt(task, candidates_list, criteria=criteria, weights=weights)

    response = await llm_provider.generate(
        prompt=prompt,
        system_prompt=system_prompt,
    )

    parsed = _safe_parse_ranking_json(response.content)
    if parsed:
        normalized = _validate_and_normalize_decision(parsed, candidates_list)
        if normalized:
            ranked_ids, scores, rationales, selected_id, confidence = normalized
            return RankDecision(
                selected_id=selected_id,
                ranked_ids=ranked_ids,
                scores=scores,
                rationales=rationales,
                confidence=confidence,
                method_used="llm",
                raw_response=response.content,
            )

    repaired = _safe_parse_ranking_json(response.content or "")
    if repaired:
        normalized = _validate_and_normalize_decision(repaired, candidates_list)
        if normalized:
            ranked_ids, scores, rationales, selected_id, confidence = normalized
            return RankDecision(
                selected_id=selected_id,
                ranked_ids=ranked_ids,
                scores=scores,
                rationales=rationales,
                confidence=confidence,
                method_used="repaired_llm",
                raw_response=response.content,
            )

    ranked_ids, scores, rationales, selected_id, confidence = _heuristic_fallback_rank(
        task,
        candidates_list,
        weights=weights,
    )
    logger.warning("LLM ranking failed; using heuristic fallback")
    return RankDecision(
        selected_id=selected_id,
        ranked_ids=ranked_ids,
        scores=scores,
        rationales=rationales,
        confidence=confidence,
        method_used="heuristic_fallback",
        raw_response=response.content,
    )