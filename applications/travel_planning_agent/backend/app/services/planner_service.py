import json
import logging
import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.travel_workflow import run_travel_workflow
from app.db.models import PlanSession, TravelPlan, User
from app.observability.metrics import record_planning_run

logger = logging.getLogger(__name__)


def _safe_text(value: Any, limit: int = 1200) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value[:limit]
    try:
        return json.dumps(value, ensure_ascii=False)[:limit]
    except TypeError:
        return str(value)[:limit]


def _try_parse_json(text: str) -> Optional[Any]:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _extract_json_block(text: str) -> Optional[Any]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = text[start : end + 1]
    return _try_parse_json(snippet)


def _extract_raw_text(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        output = node.get("output")
        if isinstance(output, str):
            return output
    return ""


def _extract_agent_output(node: Any) -> str:
    if isinstance(node, str):
        return _safe_text(node)
    if isinstance(node, dict):
        output = node.get("output")
        if output:
            return _safe_text(output)
        summary = node.get("summary")
        if summary:
            return _safe_text(summary)
    return ""


def _wrap_agent_node(node: Any) -> Dict[str, Any]:
    if isinstance(node, dict):
        payload = dict(node)
        if payload.get("output") is None:
            payload["output"] = _extract_agent_output(node)
        return payload
    if isinstance(node, str):
        return {"output": _safe_text(node)}
    return {}


def _extract_first_list(value: Any) -> Optional[List[Any]]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("days", "itinerary", "items", "plan", "schedule"):
            candidate = value.get(key)
            if isinstance(candidate, list):
                return candidate
    return None


def _normalize_itinerary(itinerary_node: Any) -> Dict[str, Any]:
    fallback = {
        "days": [
            {"day": 1, "theme": "Details pending from itinerary agent."},
        ],
        "raw": "",
    }
    if not isinstance(itinerary_node, dict):
        raw_text = _safe_text(itinerary_node)
        parsed = _extract_json_block(raw_text)
        if isinstance(parsed, dict):
            itinerary_node = parsed
        else:
            return {**fallback, "raw": raw_text}

    raw_text = _extract_raw_text(itinerary_node)
    raw_output = _safe_text(raw_text)
    parsed = None
    if raw_text:
        parsed = _extract_json_block(raw_text)
    if isinstance(parsed, dict):
        itinerary_node = {**itinerary_node, **parsed}
    days = _extract_first_list(itinerary_node)
    if not days:
        return {**fallback, "raw": raw_output}

    normalized_days = []
    for idx, day in enumerate(days[:10], start=1):
        if isinstance(day, dict):
            normalized_days.append(
                {
                    "day": day.get("day", idx),
                    "theme": day.get("theme") or day.get("title") or day.get("summary") or "",
                    "details": day.get("details") or day.get("activities") or day.get("plan"),
                }
            )
        else:
            normalized_days.append({"day": idx, "theme": _safe_text(day, 300)})

    return {
        "days": normalized_days,
        "raw": raw_output,
    }


def _normalize_budget(budget_node: Any) -> Dict[str, Any]:
    if not isinstance(budget_node, dict):
        raw_text = _safe_text(budget_node)
        parsed = _extract_json_block(raw_text)
        if isinstance(parsed, dict):
            budget_node = parsed
        else:
            return {"raw": raw_text}

    raw_text = _extract_raw_text(budget_node)
    output = _safe_text(raw_text)
    if raw_text:
        parsed = _extract_json_block(raw_text)
        if isinstance(parsed, dict):
            budget_node = {**budget_node, **parsed}
    breakdown = budget_node.get("breakdown")
    if isinstance(breakdown, dict) and breakdown:
        normalized: Dict[str, float] = {}
        for key, value in breakdown.items():
            if value is None:
                continue
            try:
                normalized[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        if normalized:
            return {"raw": output, "items": normalized}

    budget_output = budget_node.get("output")
    if isinstance(budget_output, str) and budget_output:
        return {"raw": budget_output[:1200]}

    return {"raw": output}


def _normalize_recommendations(review_node: Any) -> Dict[str, Any]:
    if not isinstance(review_node, dict):
        raw_text = _safe_text(review_node)
        parsed = _extract_json_block(raw_text)
        if isinstance(parsed, dict):
            review_node = parsed
        else:
            return {"summary": raw_text[:800], "raw": raw_text}
    summary = review_node.get("summary") or ""
    raw_text = _extract_raw_text(review_node)
    output = _safe_text(raw_text)
    if raw_text:
        parsed = _extract_json_block(raw_text)
        if isinstance(parsed, dict):
            review_node = {**review_node, **parsed}
            summary = review_node.get("summary") or summary
    recommendations = review_node.get("recommendations")
    if isinstance(recommendations, list):
        return {"summary": _safe_text(summary, 800), "raw": output, "items": recommendations}
    return {"summary": _safe_text(summary, 800), "raw": output}


def _normalize_summary_agent(summary_node: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"summary": "", "highlights": [], "daily_recommendations": []}
    if not summary_node:
        return payload

    if isinstance(summary_node, str):
        parsed = _extract_json_block(summary_node)
        if isinstance(parsed, dict):
            summary_node = parsed
        else:
            payload["summary"] = _safe_text(summary_node, 800)
            return payload

    if isinstance(summary_node, dict):
        raw_text = _extract_raw_text(summary_node)
        parsed = _extract_json_block(raw_text) if raw_text else None
        if isinstance(parsed, dict):
            summary_node = {**summary_node, **parsed}
        summary_value = summary_node.get("summary")
        if summary_value:
            payload["summary"] = _safe_text(summary_value, 800)
        highlights = summary_node.get("highlights")
        if isinstance(highlights, list):
            payload["highlights"] = [str(item) for item in highlights if item]
        daily = summary_node.get("daily_recommendations")
        if isinstance(daily, list):
            cleaned_daily = []
            for item in daily:
                if isinstance(item, dict):
                    cleaned_daily.append(
                        {
                            "day": item.get("day"),
                            "activities": [
                                str(activity)
                                for activity in (item.get("activities") or [])
                                if activity
                            ],
                        }
                    )
            payload["daily_recommendations"] = cleaned_daily
        return payload

    payload["summary"] = _safe_text(summary_node, 800)
    return payload


def _normalize_final_approval(approval_node: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"approved": None, "reason": "", "required_changes": []}
    if not approval_node:
        return payload

    if isinstance(approval_node, str):
        parsed = _extract_json_block(approval_node)
        if isinstance(parsed, dict):
            approval_node = parsed
        else:
            payload["reason"] = _safe_text(approval_node, 800)
            return payload

    if isinstance(approval_node, dict):
        raw_text = _extract_raw_text(approval_node)
        parsed = _extract_json_block(raw_text) if raw_text else None
        if isinstance(parsed, dict):
            approval_node = {**approval_node, **parsed}
        approved_value = approval_node.get("approved")
        if isinstance(approved_value, bool):
            payload["approved"] = approved_value
        reason = approval_node.get("reason")
        if reason:
            payload["reason"] = _safe_text(reason, 800)
        elif raw_text:
            payload["reason"] = _safe_text(raw_text, 800)
        required_changes = approval_node.get("required_changes")
        if isinstance(required_changes, list):
            payload["required_changes"] = [str(item) for item in required_changes if item]
        return payload

    payload["reason"] = _safe_text(approval_node, 800)
    return payload


def _summarize_node_events(node_events: Any) -> List[Dict[str, Any]]:
    if not isinstance(node_events, list):
        return []

    summaries: List[Dict[str, Any]] = []
    for event in node_events:
        if not isinstance(event, dict):
            continue
        node_id = event.get("node_id") or event.get("node") or event.get("id")
        event_type = event.get("event") or event.get("type") or "node_event"
        status = event.get("status") or event.get("state") or ""
        message = event.get("message") or event.get("detail")
        if not message:
            if status:
                message = f"{node_id} {status}" if node_id else status
            else:
                message = f"{node_id} event" if node_id else "Workflow event"

        summaries.append(
            {
                "node_id": node_id,
                "event": event_type,
                "status": status,
                "message": message,
                "timestamp": event.get("timestamp"),
            }
        )
    return summaries


async def create_plan(
    db: Session,
    user: User,
    payload: Dict[str, Any],
    event_callback=None,
) -> Dict[str, Any]:
    start_time = time.time()
    logger.info("Planner start: user_id=%s session_title=%s", user.id, payload.get("session_title"))
    session = PlanSession(user_id=user.id, title=payload["session_title"])
    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info("Planner workflow run started: session_id=%s", session.id)

    input_data = {
        "task": "Create a travel plan based on user preferences",
        "preferences": payload["preferences"],
    }
    result = await run_travel_workflow(input_data, event_callback=event_callback)
    logger.info("Planner workflow run complete: session_id=%s", session.id)

    plan = TravelPlan(
        session_id=session.id,
        request_payload=json.dumps(payload),
        response_payload=json.dumps(result),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    record_planning_run(time.time() - start_time)

    logger.info("Planner completed: session_id=%s plan_id=%s", session.id, plan.id)

    itinerary_node = result.get("itinerary_node") or {}
    budget_node = result.get("budget_node") or {}
    review_node = result.get("review_node") or {}
    summary_node = result.get("review_node") or {}
    coordinator_node = _wrap_agent_node(result.get("coordinator_node"))
    coordinator_final_node = _wrap_agent_node(
        result.get("coordinator_final_node") or result.get("coordinator_node")
    )
    final_approval = _normalize_final_approval(
        result.get("coordinator_final_node") or result.get("coordinator_node")
    )
    delegator_node = _wrap_agent_node(result.get("delegator_node"))

    itinerary = _normalize_itinerary(itinerary_node)
    budget_breakdown = _normalize_budget(budget_node)
    recommendations = _normalize_recommendations(review_node)
    summary_payload = _normalize_summary_agent(summary_node)
    summary_highlights = summary_payload.get("highlights")
    summary = summary_payload.get("summary") or recommendations.get("summary") or "Plan generated by GenXAI workflow."
    if isinstance(summary, str):
        parsed_summary = _extract_json_block(summary)
        if isinstance(parsed_summary, dict) and parsed_summary.get("summary"):
            summary = _safe_text(parsed_summary.get("summary"), 800)

    workflow_summary = {
        "input": result.get("input"),
        "node_events": result.get("node_events"),
        "progress": _summarize_node_events(result.get("node_events")),
    }

    return {
        "session_id": session.id,
        "plan_id": plan.id,
        "coordinator": coordinator_node,
        "final_approval": final_approval,
        "final_approval_raw": coordinator_final_node,
        "delegator": delegator_node,
        "itinerary": itinerary,
        "budget_breakdown": budget_breakdown,
        "recommendations": recommendations,
        "summary_highlights": summary_highlights,
        "summary_daily_recommendations": summary_payload.get("daily_recommendations"),
        "summary": summary,
        "workflow": workflow_summary,
    }
