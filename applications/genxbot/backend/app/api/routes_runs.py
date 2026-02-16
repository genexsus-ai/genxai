"""API routes for autonomous coding runs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas import ApprovalRequest, RunSession, RunTaskRequest
from app.services.orchestrator import GenXBotOrchestrator
from app.services.policy import SafetyPolicy
from app.services.store import RunStore

router = APIRouter(prefix="/runs", tags=["runs"])

_store = RunStore()
_policy = SafetyPolicy()
_orchestrator = GenXBotOrchestrator(store=_store, policy=_policy)


def get_orchestrator() -> GenXBotOrchestrator:
    return _orchestrator


@router.post("", response_model=RunSession)
def create_run(
    request: RunTaskRequest,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> RunSession:
    return orchestrator.create_run(request)


@router.get("", response_model=list[RunSession])
def list_runs(orchestrator: GenXBotOrchestrator = Depends(get_orchestrator)) -> list[RunSession]:
    return orchestrator.list_runs()


@router.get("/{run_id}", response_model=RunSession)
def get_run(
    run_id: str,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> RunSession:
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/approval", response_model=RunSession)
def decide_approval(
    run_id: str,
    request: ApprovalRequest,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> RunSession:
    run = orchestrator.decide_action(run_id, request)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
