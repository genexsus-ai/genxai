"""The planner: natural-language request → validated WorkflowPlan.

Phase 1 baseline of the generation crew. The planner calls the LLM through
``generate_structured`` (schema-enforced, with repair retries) and then
grounds the plan against the capability catalog: any capability the catalog
does not contain triggers a bounded re-plan with the offending names named
explicitly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from genxai.builder.catalog import CapabilityCatalog, build_capability_catalog
from genxai.builder.schemas import WorkflowPlan
from genxai.llm.base import LLMProvider
from genxai.utils.structured import generate_structured

logger = logging.getLogger(__name__)

# Sections larger than this show only the most request-relevant entries in
# the prompt (grounding still validates against the full catalog).
_CATALOG_SECTION_LIMIT = 40

PLANNER_SYSTEM_PROMPT = (
    "You are an expert workflow architect. You turn a user's natural-language "
    "request into a precise, minimal workflow plan. You only use capabilities "
    "from the provided catalog — never invent tool, connector, or flow names. "
    "When the request is ambiguous, record open_questions with your default "
    "assumption instead of guessing silently."
)

_PLAN_GUIDELINES = """\
Guidelines:
- Step ids are snake_case and unique; 'start' and 'end' are reserved.
- Prefer the fewest steps that satisfy the request; every step must earn its place.
- kind='agent' steps do LLM reasoning; list any catalog tools they need in capabilities.
- kind='tool' (or 'connector'/'mcp') steps invoke exactly ONE capability mechanically.
- kind='decision' steps branch: set condition, and give each dependent step a
  'when' expression describing its branch.
- kind='loop' steps repeat: set condition, optionally params.max_iterations.
- kind='flow' steps embed an agent team: set flow_pattern to a catalog flow
  capability and give team at least 2 members (role + goal each).
- depends_on expresses data/order dependencies; independent steps with the
  same dependency run in parallel automatically.
- trigger.kind is 'manual' unless the request implies a webhook or schedule."""

_EXAMPLE_PLAN = """\
Example request: "When I paste a support ticket, classify it and answer routine
tickets automatically but escalate urgent ones by email."
Example plan (JSON):
{
  "name": "Support Ticket Router",
  "description": "Classify tickets, auto-answer routine ones, escalate urgent ones",
  "trigger": {"kind": "manual", "config": {}},
  "steps": [
    {"id": "classify_ticket", "title": "Ticket Classifier",
     "description": "Label the ticket as routine or urgent", "kind": "agent",
     "capabilities": [], "depends_on": [],
     "inputs": "the raw ticket text", "outputs": "category label"},
    {"id": "answer_ticket", "title": "Support Responder",
     "description": "Draft an answer for a routine ticket", "kind": "agent",
     "capabilities": ["email_sender"], "depends_on": ["classify_ticket"],
     "when": "category == 'routine'",
     "inputs": "ticket text and category", "outputs": "reply email"},
    {"id": "escalate_ticket", "title": "Escalation Handler",
     "description": "Summarize the urgent ticket and email the on-call engineer",
     "kind": "agent", "capabilities": ["email_sender"],
     "depends_on": ["classify_ticket"], "when": "category == 'urgent'",
     "inputs": "ticket text and category", "outputs": "escalation email"}
  ],
  "open_questions": [
    {"question": "Which address should escalations go to?",
     "why_it_matters": "Urgent tickets must reach the right on-call person",
     "default_assumption": "The on-call address is provided in the workflow input"}
  ]
}"""


@dataclass(frozen=True)
class PlannerResult:
    """A grounded plan plus provenance."""

    plan: WorkflowPlan
    attempts: int
    grounding_retries: int


class PlanningError(Exception):
    """Raised when no grounded plan could be produced."""


def build_planner_prompt(
    request: str,
    catalog: CapabilityCatalog,
    *,
    feedback: str | None = None,
    max_catalog_chars: int | None = 8000,
    memory_context: str = "",
) -> str:
    """Assemble the planner prompt for a request (optionally with repair feedback)."""
    parts = [
        f"User request:\n{request}",
        _PLAN_GUIDELINES,
        catalog.to_prompt_context(
            max_chars=max_catalog_chars,
            request=request,
            section_limit=_CATALOG_SECTION_LIMIT,
        ),
        _EXAMPLE_PLAN,
    ]
    if memory_context:
        parts.append(memory_context)
    if feedback:
        parts.append(f"IMPORTANT — fix this problem from your previous plan:\n{feedback}")
    return "\n\n".join(parts)


async def plan_workflow(
    request: str,
    *,
    llm_provider: LLMProvider,
    catalog: CapabilityCatalog | None = None,
    feedback: str | None = None,
    max_repair_attempts: int = 2,
    max_grounding_retries: int = 2,
    memory: Any = None,
) -> PlannerResult:
    """Produce a catalog-grounded WorkflowPlan for a natural-language request.

    ``feedback`` lets callers (e.g. the generator's compile-retry loop) inject
    an error from a previous round. ``memory`` is an optional
    ``GenerationMemory``: similar past plans (accepted ones first) are
    injected into the prompt as extra examples. Raises
    :class:`PlanningError` when the plan still references unknown
    capabilities after all grounding retries; schema-level failures raise
    ``StructuredOutputError`` from the underlying utility.
    """
    if catalog is None:
        catalog = build_capability_catalog()

    memory_context = ""
    if memory is not None:
        try:
            memory_context = memory.render_for_prompt(memory.recall(request))
        except Exception:  # noqa: BLE001 - recall must never block planning
            logger.warning("Generation-memory recall failed", exc_info=True)

    attempts = 0
    for grounding_round in range(max_grounding_retries + 1):
        prompt = build_planner_prompt(
            request, catalog, feedback=feedback, memory_context=memory_context
        )
        result = await generate_structured(
            llm_provider=llm_provider,
            prompt=prompt,
            response_model=WorkflowPlan,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            max_repair_attempts=max_repair_attempts,
        )
        attempts += result.attempts

        unknown = catalog.unknown_capabilities(result.output.capability_names())
        if not unknown:
            return PlannerResult(
                plan=result.output,
                attempts=attempts,
                grounding_retries=grounding_round,
            )

        feedback = (
            f"The plan used capabilities that do not exist: {sorted(unknown)}. "
            "Use only capability names listed in the catalog, or drop the step."
        )
        logger.warning(
            "Plan for %r referenced unknown capabilities %s (grounding round %d)",
            request[:80],
            sorted(unknown),
            grounding_round + 1,
        )

    raise PlanningError(
        f"plan still references unknown capabilities after "
        f"{max_grounding_retries + 1} rounds: {sorted(unknown)}"
    )
