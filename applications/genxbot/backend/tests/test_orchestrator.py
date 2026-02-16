from app.schemas import ApprovalRequest, RunTaskRequest
from app.services.orchestrator import GenXBotOrchestrator
from app.services.policy import SafetyPolicy
from app.services.store import RunStore


def build_orchestrator() -> GenXBotOrchestrator:
    return GenXBotOrchestrator(store=RunStore(), policy=SafetyPolicy())


def test_create_run_generates_plan_and_pending_actions() -> None:
    orchestrator = build_orchestrator()
    run = orchestrator.create_run(
        RunTaskRequest(goal="Add API tests and fix lint", repo_path="/tmp/repo")
    )

    assert run.id.startswith("run_")
    assert run.status == "awaiting_approval"
    assert len(run.plan_steps) == 4
    assert len(run.pending_actions) >= 1
    assert len(run.timeline) >= 2


def test_approval_executes_action_and_updates_artifacts() -> None:
    orchestrator = build_orchestrator()
    run = orchestrator.create_run(
        RunTaskRequest(goal="Implement feature", repo_path="/tmp/repo")
    )

    action = run.pending_actions[0]
    updated = orchestrator.decide_action(
        run.id,
        ApprovalRequest(action_id=action.id, approve=True, comment="Proceed"),
    )

    assert updated is not None
    assert any(a.status == "executed" for a in updated.pending_actions)
    assert len(updated.artifacts) >= 2
    assert any(evt.event == "action_executed" for evt in updated.timeline)
