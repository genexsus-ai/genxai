"""Core autonomous coding orchestration service (prototype)."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.schemas import (
    ApprovalRequest,
    Artifact,
    PlanStep,
    ProposedAction,
    RunSession,
    RunTaskRequest,
    TimelineEvent,
)
from app.services.policy import SafetyPolicy
from app.services.store import RunStore


def _ensure_repo_root_on_path() -> None:
    """Ensure local repo root is importable so `import genxai` works from app folder."""
    repo_root = Path(__file__).resolve().parents[5]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_path()

from genxai import AgentFactory, AgentRuntime, CriticReviewFlow, MemorySystem, ToolRegistry  # noqa: E402
from genxai.tools import Tool  # noqa: E402
from genxai.tools.builtin import *  # noqa: F403,F401,E402 - register built-in tools


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GenXBotOrchestrator:
    """Orchestrates planning, approval, and execution timeline for runs."""

    def __init__(self, store: RunStore, policy: SafetyPolicy) -> None:
        self._store = store
        self._policy = policy
        self._settings = get_settings()
        self._genxai_runtime_ctx: dict[str, dict[str, Any]] = {}

    def _tool_map(self) -> dict[str, Tool]:
        return {tool.metadata.name: tool for tool in ToolRegistry.list_all()}

    def _build_genxai_stack(self, run_id: str, goal: str) -> dict[str, Any]:
        tools = self._tool_map()
        preferred_tools = [
            "directory_scanner",
            "file_reader",
            "file_writer",
            "code_executor",
            "data_validator",
            "regex_matcher",
        ]
        enabled_tools = [name for name in preferred_tools if name in tools]

        planner = AgentFactory.create_agent(
            id=f"planner_{run_id}",
            role="Codebase Planner",
            goal="Produce safe, testable coding plans from user goals",
            llm_model="gpt-4",
            tools=enabled_tools,
            enable_memory=True,
        )
        executor = AgentFactory.create_agent(
            id=f"executor_{run_id}",
            role="Code Executor",
            goal="Propose and execute coding actions safely",
            llm_model="gpt-4",
            tools=enabled_tools,
            enable_memory=True,
        )
        reviewer = AgentFactory.create_agent(
            id=f"reviewer_{run_id}",
            role="Code Reviewer",
            goal="Review plans and actions for safety and quality",
            llm_model="gpt-4",
            tools=enabled_tools,
            enable_memory=True,
        )

        openai_key = os.getenv("OPENAI_API_KEY")
        planner_runtime = AgentRuntime(agent=planner, openai_api_key=openai_key)
        executor_runtime = AgentRuntime(agent=executor, openai_api_key=openai_key)
        reviewer_runtime = AgentRuntime(agent=reviewer, openai_api_key=openai_key)

        planner_runtime.set_tools(tools)
        executor_runtime.set_tools(tools)
        reviewer_runtime.set_tools(tools)

        memory = MemorySystem(
            agent_id=f"genxbot_{run_id}",
            persistence_enabled=True,
            persistence_path=Path(".genxai/memory/genxbot"),
        )
        planner_runtime.set_memory(memory)
        executor_runtime.set_memory(memory)
        reviewer_runtime.set_memory(memory)

        return {
            "planner": planner,
            "executor": executor,
            "reviewer": reviewer,
            "planner_runtime": planner_runtime,
            "executor_runtime": executor_runtime,
            "reviewer_runtime": reviewer_runtime,
            "memory": memory,
            "tools": tools,
            "goal": goal,
        }

    async def _run_genxai_pipeline(
        self,
        run_id: str,
        goal: str,
        repo_path: str,
        context: str | None,
    ) -> dict[str, Any]:
        stack = self._genxai_runtime_ctx[run_id]
        planner_runtime: AgentRuntime = stack["planner_runtime"]
        executor_runtime: AgentRuntime = stack["executor_runtime"]
        reviewer_runtime: AgentRuntime = stack["reviewer_runtime"]

        planner_task = (
            "Create a concise execution plan for the coding goal. "
            "Return bullet points with repo analysis, code edits, and tests."
        )
        planner_result = await planner_runtime.execute(
            task=planner_task,
            context={"goal": goal, "repo_path": repo_path, "context": context or ""},
        )
        plan_text = planner_result.get("output", "")

        executor_task = (
            "Given the plan, propose two actions in plain text: one command and one edit. "
            "Prefer safe test/lint command first."
        )
        executor_result = await executor_runtime.execute(
            task=executor_task,
            context={
                "goal": goal,
                "repo_path": repo_path,
                "plan": plan_text,
            },
        )

        review_flow = CriticReviewFlow(
            agents=[stack["executor"], stack["reviewer"]],
            max_iterations=1,
        )
        review_state = await review_flow.run(
            input_data={"goal": goal, "repo_path": repo_path},
            state={
                "task": "Review the proposed coding approach for risks and completeness.",
                "critic_task": "Provide concrete risk feedback and improvements.",
                "accept": True,
            },
            max_iterations=5,
        )

        return {
            "plan_text": plan_text,
            "executor_output": executor_result.get("output", ""),
            "review": review_state.get("last_critique", {}),
        }

    def create_run(self, request: RunTaskRequest) -> RunSession:
        plan_steps = [
            PlanStep(title="Ingest repository and identify project context"),
            PlanStep(title="Generate implementation plan from goal"),
            PlanStep(title="Propose safe code edits"),
            PlanStep(title="Run lint/tests and summarize result"),
        ]
        base_actions = [
            ProposedAction(
                action_type="command",
                description="Run unit tests to establish baseline",
                command="pytest -q",
            ),
            ProposedAction(
                action_type="edit",
                description="Apply patch for requested feature implementation",
                file_path=f"{request.repo_path}/TARGET_FILE.py",
                patch="*** simulated patch ***",
            ),
        ]

        run = RunSession(
            goal=request.goal,
            repo_path=request.repo_path,
            status="created",
            plan_steps=plan_steps,
            pending_actions=[],
            memory_summary=(
                "Initial memory: user asked for autonomous coding workflow with "
                "repo ingest, plan, edit, and test loop."
            ),
            timeline=[
                TimelineEvent(
                    agent="system",
                    event="genxai_bootstrap",
                    content="Initializing GenXAI agents, runtime, tools, and memory.",
                )
            ],
            artifacts=[],
        )
        run.created_at = _now()
        run.updated_at = run.created_at

        self._genxai_runtime_ctx[run.id] = self._build_genxai_stack(run.id, request.goal)

        openai_key = os.getenv("OPENAI_API_KEY")
        pipeline_output: dict[str, Any] = {}
        if openai_key:
            try:
                pipeline_output = asyncio.run(
                    self._run_genxai_pipeline(
                        run_id=run.id,
                        goal=request.goal,
                        repo_path=request.repo_path,
                        context=request.context,
                    )
                )
                run.timeline.append(
                    TimelineEvent(
                        agent="genxai_runtime",
                        event="pipeline_executed",
                        content="Planner/executor/reviewer pipeline completed with live LLM runtime.",
                    )
                )
            except Exception as exc:
                run.timeline.append(
                    TimelineEvent(
                        agent="genxai_runtime",
                        event="pipeline_fallback",
                        content=f"Live pipeline failed, fallback activated: {exc}",
                    )
                )
        else:
            run.timeline.append(
                TimelineEvent(
                    agent="genxai_runtime",
                    event="pipeline_fallback",
                    content="OPENAI_API_KEY missing; using deterministic fallback while keeping GenXAI wiring active.",
                )
            )

        proposed_actions = base_actions
        if pipeline_output.get("executor_output"):
            proposed_actions[1].patch = (
                "*** genxai-proposed patch draft ***\n"
                f"{pipeline_output['executor_output'][:1200]}"
            )

        for action in proposed_actions:
            action.safe = action.action_type == "command" and bool(
                action.command and self._policy.is_safe_command(action.command)
            )

        has_gate = any(self._policy.requires_approval(a) for a in proposed_actions)
        status = "awaiting_approval" if has_gate else "running"
        run.status = status
        run.pending_actions = proposed_actions
        run.timeline.extend(
            [
                TimelineEvent(
                    agent="planner",
                    event="plan_created",
                    content="Generated 4-step autonomous coding plan.",
                ),
                TimelineEvent(
                    agent="executor",
                    event="actions_proposed",
                    content=f"Proposed {len(proposed_actions)} actions; awaiting approval.",
                ),
            ]
        )
        run.artifacts.append(
            Artifact(
                kind="plan",
                title="Initial execution plan",
                content=pipeline_output.get(
                    "plan_text",
                    "\n".join(f"- {step.title}" for step in plan_steps),
                ),
            )
        )
        if pipeline_output.get("review"):
            run.artifacts.append(
                Artifact(
                    kind="summary",
                    title="Critic review feedback",
                    content=str(pipeline_output["review"]),
                )
            )

        run.memory_summary = (
            "GenXAI memory initialized for this run. "
            "Planner/executor/reviewer context is tracked via MemorySystem."
        )
        run.updated_at = _now()
        return self._store.create(run)

    def get_run(self, run_id: str) -> RunSession | None:
        return self._store.get(run_id)

    def list_runs(self) -> list[RunSession]:
        return list(self._store.list_runs())

    def decide_action(self, run_id: str, approval: ApprovalRequest) -> RunSession | None:
        run = self._store.get(run_id)
        if not run:
            return None

        chosen = next((a for a in run.pending_actions if a.id == approval.action_id), None)
        if not chosen:
            return run

        chosen.status = "approved" if approval.approve else "rejected"
        run.timeline.append(
            TimelineEvent(
                agent="user",
                event="approval_decision",
                content=(
                    f"Action {chosen.id} {chosen.status}. "
                    f"Comment: {approval.comment or 'n/a'}"
                ),
            )
        )

        if approval.approve:
            chosen.status = "executed"
            run.timeline.append(
                TimelineEvent(
                    agent="executor",
                    event="action_executed",
                    content=f"Executed {chosen.action_type}: {chosen.description}",
                )
            )
            run.artifacts.append(
                Artifact(
                    kind="command_output" if chosen.action_type == "command" else "diff",
                    title=f"Result for {chosen.id}",
                    content=(
                        f"Command simulated: {chosen.command}"
                        if chosen.action_type == "command"
                        else f"Patch simulated for {chosen.file_path}\n{chosen.patch or ''}"
                    ),
                )
            )

        all_done = all(action.status in {"executed", "rejected"} for action in run.pending_actions)
        if all_done:
            run.status = "completed"
            run.timeline.append(
                TimelineEvent(
                    agent="reviewer",
                    event="run_completed",
                    content="Run completed with all actions resolved.",
                )
            )
            run.artifacts.append(
                Artifact(
                    kind="summary",
                    title="Run summary",
                    content="Prototype execution complete. Integrate real tool runners next.",
                )
            )
        else:
            run.status = "awaiting_approval"

        run.updated_at = _now()
        return self._store.update(run)
