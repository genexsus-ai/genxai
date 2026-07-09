"""The generation crew: planner → delegator → designer workers → review.

Phase 2 of NL workflow generation. The Phase 1 planner produces the
``WorkflowPlan``; here a delegator LLM routes the plan's steps as work
packets to specialized designer workers (agent designer, node designer),
whose structured outputs are merged back into the plan by pure code. A
reviewer then judges the refined plan against the original request, and
rejections re-enter planning as feedback for a bounded number of rounds.

Worker dispatch runs in dependency waves — packets in the same wave execute
concurrently. Delegation is LLM-driven with a deterministic fallback, so a
malformed delegation degrades gracefully instead of failing the run.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from genxai.builder.catalog import CapabilityCatalog, build_capability_catalog
from genxai.builder.compiler import DEFAULT_MODEL, CompileError, compile_plan
from genxai.builder.generator import (
    GenerationError,
    _metrics,
    _record_generation,
    _record_metrics,
    emit_event,
)
from genxai.builder.planner import plan_workflow
from genxai.builder.schemas import DelegationPlan, PlanStep, WorkflowPlan, WorkPacket
from genxai.llm.base import LLMProvider
from genxai.utils.structured import StructuredOutputError, generate_structured

logger = logging.getLogger(__name__)

AGENT_DESIGNER = "agent_designer"
NODE_DESIGNER = "node_designer"
WORKER_TAGS = (AGENT_DESIGNER, NODE_DESIGNER)

DELEGATOR_SYSTEM_PROMPT = (
    "You are a delegation lead. You split a workflow plan's steps into work "
    "packets and route each packet to the right specialist worker. Every "
    "step must be covered by exactly one packet."
)

AGENT_DESIGNER_SYSTEM_PROMPT = (
    "You are an expert AI-agent designer. For each assigned workflow step "
    "you craft the agent that executes it: a sharp role, a measurable goal, "
    "a grounding backstory, a temperature suited to the work, and only "
    "tools that exist in the catalog."
)

NODE_DESIGNER_SYSTEM_PROMPT = (
    "You are an expert workflow-node designer. For each assigned step you "
    "pick the exact capability to invoke, its parameters, and precise "
    "conditions for decisions and loops. You never invent capability names."
)

REVIEWER_SYSTEM_PROMPT = (
    "You are a critical workflow reviewer. Judge whether the plan fully and "
    "minimally satisfies the user's request. Approve only when every "
    "requirement is covered; otherwise list concrete, actionable issues."
)


class AgentSpec(BaseModel):
    """Agent designer output for one agent step."""

    step_id: str
    role: str
    goal: str
    backstory: str = ""
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    tools: list[str] = Field(default_factory=list)


class AgentDesignOutput(BaseModel):
    specs: list[AgentSpec]


class NodeSpec(BaseModel):
    """Node designer output for one non-agent step."""

    step_id: str
    capability: str | None = Field(
        None, description="The single catalog capability this step invokes"
    )
    params: dict[str, Any] = Field(default_factory=dict)
    condition: str | None = None


class NodeDesignOutput(BaseModel):
    specs: list[NodeSpec]


class ReviewVerdict(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class CrewGenerationResult:
    """A crew-generated workflow with full provenance."""

    workflow: dict[str, Any]
    plan: WorkflowPlan
    delegation: DelegationPlan
    review: ReviewVerdict | None
    llm_attempts: int
    rounds: int
    delegation_fallback: bool = False
    warnings: list[str] = field(default_factory=list)
    generation_id: str | None = None

    @property
    def open_questions(self):
        return self.plan.open_questions


def route_deterministically(plan: WorkflowPlan) -> DelegationPlan:
    """Fallback delegation: agent steps → agent designer, the rest → node designer."""
    agent_steps = [step.id for step in plan.steps if step.kind == "agent"]
    other_steps = [step.id for step in plan.steps if step.kind != "agent"]
    packets = []
    if agent_steps:
        packets.append(
            WorkPacket(
                id="design_agents",
                worker=AGENT_DESIGNER,
                objective="Design the agents for the assigned steps",
                step_ids=agent_steps,
            )
        )
    if other_steps:
        packets.append(
            WorkPacket(
                id="design_nodes",
                worker=NODE_DESIGNER,
                objective="Design the node configuration for the assigned steps",
                step_ids=other_steps,
            )
        )
    return DelegationPlan(packets=packets)


def _plan_steps_json(plan: WorkflowPlan, step_ids: list[str] | None = None) -> str:
    steps = plan.steps if step_ids is None else [s for s in plan.steps if s.id in step_ids]
    payload = {
        "name": plan.name,
        "description": plan.description,
        "steps": [step.model_dump(exclude_none=True) for step in steps],
    }
    return json.dumps(payload, indent=2, default=str)


async def delegate_plan(
    request: str,
    plan: WorkflowPlan,
    *,
    llm_provider: LLMProvider,
    max_repair_attempts: int = 1,
) -> tuple[DelegationPlan, bool, int]:
    """LLM delegation with deterministic fallback.

    Returns (delegation, used_fallback, llm_attempts).
    """
    prompt = (
        f"User request:\n{request}\n\n"
        f"Workflow plan steps:\n{_plan_steps_json(plan)}\n\n"
        f"Workers: '{AGENT_DESIGNER}' designs agents for kind='agent' steps; "
        f"'{NODE_DESIGNER}' configures every other step kind.\n"
        "Route every step id into exactly one packet; a packet's steps must "
        "all belong to its worker's specialty."
    )
    try:
        result = await generate_structured(
            llm_provider=llm_provider,
            prompt=prompt,
            response_model=DelegationPlan,
            system_prompt=DELEGATOR_SYSTEM_PROMPT,
            max_repair_attempts=max_repair_attempts,
        )
        delegation = result.output
        delegation.validate_against_plan(plan)
        unknown_workers = {p.worker for p in delegation.packets} - set(WORKER_TAGS)
        if unknown_workers:
            raise ValueError(f"unknown workers: {sorted(unknown_workers)}")
        return delegation, False, result.attempts
    except (StructuredOutputError, ValueError) as exc:
        logger.warning("Delegation failed (%s); using deterministic routing", exc)
        return route_deterministically(plan), True, 0


async def run_agent_designer(
    packet: WorkPacket,
    plan: WorkflowPlan,
    catalog: CapabilityCatalog,
    *,
    llm_provider: LLMProvider,
) -> AgentDesignOutput:
    steps_json = _plan_steps_json(plan, packet.step_ids)
    prompt = (
        f"Design one agent per assigned step.\n"
        f"Packet objective: {packet.objective}\n"
        f"Assigned steps:\n{steps_json}\n\n"
        f"{catalog.to_prompt_context(max_chars=6000, request=steps_json, section_limit=25)}\n\n"
        "Return one spec per assigned step_id. Use only catalog tool names."
    )
    result = await generate_structured(
        llm_provider=llm_provider,
        prompt=prompt,
        response_model=AgentDesignOutput,
        system_prompt=AGENT_DESIGNER_SYSTEM_PROMPT,
    )
    return result.output


async def run_node_designer(
    packet: WorkPacket,
    plan: WorkflowPlan,
    catalog: CapabilityCatalog,
    *,
    llm_provider: LLMProvider,
) -> NodeDesignOutput:
    steps_json = _plan_steps_json(plan, packet.step_ids)
    prompt = (
        f"Configure each assigned workflow step.\n"
        f"Packet objective: {packet.objective}\n"
        f"Assigned steps:\n{steps_json}\n\n"
        f"{catalog.to_prompt_context(max_chars=6000, request=steps_json, section_limit=25)}\n\n"
        "Return one spec per assigned step_id. For tool/connector/mcp steps "
        "set capability to exactly one catalog name; for decision/loop steps "
        "set a precise condition."
    )
    result = await generate_structured(
        llm_provider=llm_provider,
        prompt=prompt,
        response_model=NodeDesignOutput,
        system_prompt=NODE_DESIGNER_SYSTEM_PROMPT,
    )
    return result.output


def apply_specs(
    plan: WorkflowPlan,
    agent_specs: list[AgentSpec],
    node_specs: list[NodeSpec],
    catalog: CapabilityCatalog,
) -> tuple[WorkflowPlan, list[str]]:
    """Merge worker outputs into the plan. Returns (new plan, warnings).

    Specs for unknown steps and tools/capabilities missing from the catalog
    are dropped with a warning rather than failing the round.
    """
    warnings: list[str] = []
    steps_by_id: dict[str, PlanStep] = {step.id: step for step in plan.steps}
    known = catalog.names()

    for spec in agent_specs:
        step = steps_by_id.get(spec.step_id)
        if step is None or step.kind != "agent":
            warnings.append(f"agent spec for unknown/non-agent step '{spec.step_id}' dropped")
            continue
        valid_tools = [tool for tool in spec.tools if tool in known]
        dropped = set(spec.tools) - set(valid_tools)
        if dropped:
            warnings.append(f"step '{step.id}': unknown tools {sorted(dropped)} dropped")
        steps_by_id[step.id] = step.model_copy(
            update={
                "title": spec.role,
                "description": spec.goal,
                "backstory": spec.backstory,
                "temperature": spec.temperature,
                "capabilities": valid_tools,
            }
        )

    for spec in node_specs:
        step = steps_by_id.get(spec.step_id)
        if step is None or step.kind == "agent":
            warnings.append(f"node spec for unknown/agent step '{spec.step_id}' dropped")
            continue
        update: dict[str, Any] = {}
        if spec.capability:
            if spec.capability in known:
                update["capabilities"] = [spec.capability]
            else:
                warnings.append(f"step '{step.id}': unknown capability '{spec.capability}' dropped")
        if spec.params:
            update["params"] = {**step.params, **spec.params}
        if spec.condition and step.kind in {"decision", "loop"}:
            update["condition"] = spec.condition
        if update:
            steps_by_id[step.id] = step.model_copy(update=update)

    merged = plan.model_copy(update={"steps": [steps_by_id[step.id] for step in plan.steps]})
    # Re-run model validation on the merged plan.
    return WorkflowPlan.model_validate(merged.model_dump()), warnings


async def review_plan(
    request: str,
    plan: WorkflowPlan,
    *,
    llm_provider: LLMProvider,
) -> ReviewVerdict:
    prompt = (
        f"User request:\n{request}\n\n"
        f"Refined workflow plan:\n{_plan_steps_json(plan)}\n\n"
        "Does this plan fully and minimally satisfy the request? Approve, or "
        "list concrete issues to fix."
    )
    result = await generate_structured(
        llm_provider=llm_provider,
        prompt=prompt,
        response_model=ReviewVerdict,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
    )
    return result.output


async def crew_generate_workflow(
    request: str,
    *,
    llm_provider: LLMProvider,
    catalog: CapabilityCatalog | None = None,
    default_model: str = DEFAULT_MODEL,
    max_rounds: int = 2,
    enable_review: bool = True,
    on_event: Any = None,
    memory: Any = None,
    **planner_kwargs: Any,
) -> CrewGenerationResult:
    """Generate a workflow with the full planner→delegator→worker crew.

    Each round: plan → delegate → design (waves, concurrent) → merge →
    review → compile. Review rejections and compile errors become planner
    feedback for the next round; the final round compiles regardless of the
    review verdict, which is returned for the caller to surface.

    ``on_event(stage, data)`` receives progress notifications (``planning``,
    ``planned``, ``delegating``, ``delegated``, ``designing``, ``designed``,
    ``reviewing``, ``reviewed``, ``compile_failed``, ``compiled``).
    """
    if catalog is None:
        catalog = build_capability_catalog()

    collector = _metrics()
    started = time.monotonic()
    feedback: str | None = None
    llm_attempts = 0
    last_state: dict[str, Any] = {}

    for round_index in range(max_rounds):
        emit_event(on_event, "planning", round=round_index + 1)
        planned = await plan_workflow(
            request,
            llm_provider=llm_provider,
            catalog=catalog,
            feedback=feedback,
            memory=memory,
            **planner_kwargs,
        )
        llm_attempts += planned.attempts
        emit_event(
            on_event,
            "planned",
            name=planned.plan.name,
            steps=len(planned.plan.steps),
            open_questions=len(planned.plan.open_questions),
        )

        emit_event(on_event, "delegating")
        delegation, used_fallback, attempts = await delegate_plan(
            request, planned.plan, llm_provider=llm_provider
        )
        llm_attempts += attempts
        emit_event(
            on_event,
            "delegated",
            packets=[
                {"id": p.id, "worker": p.worker, "steps": p.step_ids} for p in delegation.packets
            ],
            fallback=used_fallback,
        )

        agent_specs: list[AgentSpec] = []
        node_specs: list[NodeSpec] = []
        for wave in delegation.dispatch_waves():
            for packet in wave:
                emit_event(on_event, "designing", packet=packet.id, worker=packet.worker)
            outputs = await asyncio.gather(
                *(
                    (
                        run_agent_designer(packet, planned.plan, catalog, llm_provider=llm_provider)
                        if packet.worker == AGENT_DESIGNER
                        else run_node_designer(
                            packet, planned.plan, catalog, llm_provider=llm_provider
                        )
                    )
                    for packet in wave
                )
            )
            llm_attempts += len(outputs)
            for output in outputs:
                if isinstance(output, AgentDesignOutput):
                    agent_specs.extend(output.specs)
                else:
                    node_specs.extend(output.specs)

        merged, warnings = apply_specs(planned.plan, agent_specs, node_specs, catalog)
        emit_event(
            on_event,
            "designed",
            agent_specs=len(agent_specs),
            node_specs=len(node_specs),
            warnings=warnings,
        )

        review: ReviewVerdict | None = None
        if enable_review:
            emit_event(on_event, "reviewing")
            review = await review_plan(request, merged, llm_provider=llm_provider)
            llm_attempts += 1
            emit_event(on_event, "reviewed", approved=review.approved, issues=review.issues)

        last_state = {
            "plan": merged,
            "delegation": delegation,
            "review": review,
            "fallback": used_fallback,
            "warnings": warnings,
        }

        final_round = round_index == max_rounds - 1
        if review is not None and not review.approved and not final_round:
            feedback = "The reviewer rejected the plan. Issues to fix:\n- " + "\n- ".join(
                review.issues or ["(no specific issues given)"]
            )
            logger.info("Review rejected plan (round %d): %s", round_index + 1, review.issues)
            continue

        try:
            workflow = compile_plan(merged, default_model=default_model)
        except CompileError as exc:
            emit_event(on_event, "compile_failed", error=str(exc), round=round_index + 1)
            if final_round:
                _record_metrics(
                    collector,
                    "crew",
                    success=False,
                    started=started,
                    llm_attempts=llm_attempts,
                )
                raise GenerationError(
                    f"crew could not compile a valid workflow after {max_rounds} " f"rounds: {exc}",
                    plan=merged,
                ) from exc
            feedback = str(exc)
            logger.warning("Crew compile failed (round %d): %s", round_index + 1, exc)
            continue

        emit_event(on_event, "compiled", nodes=len(workflow["graph"]["nodes"]))
        generation_id = _record_generation(memory, request, merged)
        _record_metrics(collector, "crew", success=True, started=started, llm_attempts=llm_attempts)
        return CrewGenerationResult(
            workflow=workflow,
            plan=merged,
            delegation=delegation,
            review=review,
            llm_attempts=llm_attempts,
            rounds=round_index + 1,
            delegation_fallback=used_fallback,
            warnings=warnings,
            generation_id=generation_id,
        )

    # Only reachable when the last round's review was rejected AND compile
    # succeeded is false — but the final round always attempts compilation,
    # so reaching here means compilation raised and was re-raised above.
    raise GenerationError(
        f"crew exhausted {max_rounds} rounds without a valid workflow",
        plan=last_state.get("plan"),
    )
