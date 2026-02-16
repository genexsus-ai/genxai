"""API routes for autonomous coding runs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import get_settings
from app.schemas import (
    ApprovalRequest,
    ApproverAllowlistResponse,
    ApproverAllowlistUpdateRequest,
    ChannelInboundRequest,
    ChannelInboundResponse,
    ChannelMetricsSnapshot,
    ChannelSessionSnapshot,
    ChannelTrustPolicy,
    OutboundRetryQueueSnapshot,
    ChannelTrustPolicyUpdateRequest,
    AuditEntry,
    ConnectorTriggerRequest,
    ConnectorTriggerResponse,
    EvaluationMetrics,
    PairingApprovalRequest,
    PairingApprovalResponse,
    PendingPairingCode,
    QueueJobStatusResponse,
    RerunFailedStepRequest,
    RunSession,
    RunTaskRequest,
)
from app.services.channels import parse_channel_event
from app.services.channels import parse_channel_command
from app.services.channel_outbound import (
    ChannelOutboundService,
    format_outbound_action_decision,
    format_outbound_run_created,
    format_outbound_status,
)
from app.services.channel_observability import ChannelObservabilityService
from app.services.channel_sessions import ChannelSessionService
from app.services.channel_trust import ChannelTrustService
from app.services.orchestrator import GenXBotOrchestrator
from app.services.policy import SafetyPolicy
from app.services.queue import RunQueueService
from app.services.rate_limit import InMemoryRateLimiter, build_rate_limiter_dependency
from app.services.store import RunStore
from app.services.webhook_security import WebhookSecurityService
from app.services.outbound_retry_queue import OutboundRetryQueueService

_settings = get_settings()
_store = (
    RunStore(db_path=_settings.run_store_path)
    if _settings.run_store_backend.lower() == "sqlite"
    else RunStore()
)
_policy = SafetyPolicy()
_orchestrator = GenXBotOrchestrator(store=_store, policy=_policy)
_run_queue = RunQueueService(
    orchestrator=_orchestrator,
    worker_enabled=_settings.queue_worker_enabled,
)
_rate_limiter = InMemoryRateLimiter(
    requests_per_window=_settings.rate_limit_requests,
    window_seconds=_settings.rate_limit_window_seconds,
)
_rate_limit_dependency = build_rate_limiter_dependency(
    limiter=_rate_limiter,
    enabled=_settings.rate_limit_enabled,
)

_channel_state_db = (
    _settings.channel_state_sqlite_path
    if _settings.channel_state_backend.strip().lower() == "sqlite"
    else None
)

_channel_trust = ChannelTrustService(db_path=_channel_state_db)
_channel_sessions = ChannelSessionService(db_path=_channel_state_db)
_channel_outbound = ChannelOutboundService(
    enabled=_settings.channel_outbound_enabled,
    slack_webhook_url=_settings.slack_outbound_webhook_url,
    telegram_bot_token=_settings.telegram_bot_token,
    telegram_api_base_url=_settings.telegram_api_base_url,
)
_channel_observability = ChannelObservabilityService()
_outbound_retry_queue = OutboundRetryQueueService(
    send_fn=lambda channel, channel_id, text, thread_id: _channel_outbound.send(
        channel=channel,
        channel_id=channel_id,
        text=text,
        thread_id=thread_id,
    ),
    worker_enabled=_settings.channel_outbound_retry_worker_enabled,
    max_attempts=_settings.channel_outbound_retry_max_attempts,
    backoff_seconds=_settings.channel_outbound_retry_backoff_seconds,
)
_webhook_security = WebhookSecurityService(
    enabled=_settings.channel_webhook_security_enabled,
    slack_secret=_settings.slack_signing_secret,
    telegram_secret=_settings.telegram_webhook_secret,
    slack_secrets=[s.strip() for s in _settings.slack_signing_secrets.split(",") if s.strip()],
    telegram_secrets=[s.strip() for s in _settings.telegram_webhook_secrets.split(",") if s.strip()],
    replay_window_seconds=_settings.webhook_replay_window_seconds,
)
_command_approver_allowlist = {
    v.strip() for v in _settings.channel_command_approver_allowlist.split(",") if v.strip()
}


def _send_outbound(
    *,
    channel: str,
    channel_id: str,
    text: str,
    thread_id: str | None,
) -> str:
    delivery = _channel_outbound.send(
        channel=channel,
        channel_id=channel_id,
        text=text,
        thread_id=thread_id,
    )
    if delivery.startswith("failed:"):
        job = _outbound_retry_queue.enqueue(
            channel=channel,
            channel_id=channel_id,
            text=text,
            thread_id=thread_id,
        )
        delivery = f"{delivery};queued_retry:{job.id}"

    _channel_observability.record_outbound(channel=channel, delivery_status=delivery)
    return delivery

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    dependencies=[Depends(_rate_limit_dependency)],
)


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


@router.get("/metrics", response_model=EvaluationMetrics)
def get_metrics(
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> EvaluationMetrics:
    return orchestrator.get_evaluation_metrics()


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


@router.post("/{run_id}/rerun-failed-step", response_model=RunSession)
def rerun_failed_step(
    run_id: str,
    request: RerunFailedStepRequest,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> RunSession:
    run = orchestrator.rerun_failed_step(run_id, request)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/{run_id}/audit", response_model=list[AuditEntry])
def get_run_audit(
    run_id: str,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> list[AuditEntry]:
    audit = orchestrator.get_run_audit_log(run_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return audit


@router.post("/triggers/{connector}", response_model=ConnectorTriggerResponse)
def trigger_connector_run(
    connector: str,
    request: ConnectorTriggerRequest,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> ConnectorTriggerResponse:
    if connector != request.connector:
        raise HTTPException(
            status_code=400,
            detail="Path connector and payload connector mismatch",
        )
    run = orchestrator.create_run_from_connector(request)
    return ConnectorTriggerResponse(
        connector=request.connector,
        event_type=request.event_type,
        run=run,
    )


@router.post("/channels/{channel}", response_model=ChannelInboundResponse)
def ingest_channel_event(
    channel: str,
    request: ChannelInboundRequest,
    raw_request: Request,
    orchestrator: GenXBotOrchestrator = Depends(get_orchestrator),
) -> ChannelInboundResponse:
    trace_id = _channel_observability.new_trace_id()
    if channel != request.channel:
        raise HTTPException(
            status_code=400,
            detail="Path channel and payload channel mismatch",
        )

    try:
        normalized = parse_channel_event(
            channel=request.channel,
            event_type=request.event_type,
            payload=request.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        _webhook_security.verify(channel=request.channel, headers=dict(raw_request.headers))
    except ValueError as exc:
        if "Replay detected" in str(exc):
            _channel_observability.record_replay_blocked()
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if not _channel_trust.is_trusted(request.channel, normalized.user_id):
        pending = _channel_trust.issue_pairing_code(request.channel, normalized.user_id)
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Sender is not paired/allowlisted for this channel",
                "pairing_code": pending.code,
                "channel": pending.channel,
                "user_id": pending.user_id,
            },
        )

    session_key = _channel_sessions.build_session_key(
        channel=normalized.channel,
        channel_id=normalized.channel_id,
        thread_id=normalized.thread_id,
        user_id=normalized.user_id,
    )
    command, args = parse_channel_command(normalized.text)
    _channel_observability.record_inbound(
        channel=normalized.channel,
        command=command or "run",
    )

    if command == "status":
        run_id = args.split()[0] if args else _channel_sessions.get_latest_run(session_key)
        if not run_id:
            outbound_text = "No run context found for this conversation. Start with /run <goal>."
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )
        run = orchestrator.get_run(run_id)
        if not run:
            outbound_text = f"Run {run_id} not found."
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )
        outbound_text = format_outbound_status(run)
        delivery = _send_outbound(
            channel=normalized.channel,
            channel_id=normalized.channel_id,
            thread_id=normalized.thread_id,
            text=outbound_text,
        )
        return ChannelInboundResponse(
            channel=request.channel,
            event_type=request.event_type,
            run=run,
            command=command,
            outbound_text=outbound_text,
            outbound_delivery=delivery,
            session_key=session_key,
            trace_id=trace_id,
        )

    if command in {"approve", "reject"}:
        if _command_approver_allowlist and normalized.user_id not in _command_approver_allowlist:
            outbound_text = (
                f"User {normalized.user_id} is not allowed to execute /{command}. "
                "Ask an approved operator to review this action."
            )
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )

        parts = args.split()
        if not parts:
            outbound_text = "Usage: /approve <action_id> [run_id] or /reject <action_id> [run_id]"
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )
        action_id = parts[0]
        run_id = parts[1] if len(parts) > 1 else _channel_sessions.get_latest_run(session_key)
        if not run_id:
            outbound_text = "No run context found. Provide run_id or start with /run <goal>."
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )

        run = orchestrator.decide_action(
            run_id,
            ApprovalRequest(
                action_id=action_id,
                approve=command == "approve",
                actor=f"{normalized.channel}:{normalized.user_id}",
                actor_role="approver",
            ),
        )
        if not run:
            outbound_text = f"Run {run_id} not found."
            delivery = _send_outbound(
                channel=normalized.channel,
                channel_id=normalized.channel_id,
                thread_id=normalized.thread_id,
                text=outbound_text,
            )
            return ChannelInboundResponse(
                channel=request.channel,
                event_type=request.event_type,
                command=command,
                outbound_text=outbound_text,
                outbound_delivery=delivery,
                session_key=session_key,
                trace_id=trace_id,
            )

        outbound_text = format_outbound_action_decision(run, approved=command == "approve")
        delivery = _send_outbound(
            channel=normalized.channel,
            channel_id=normalized.channel_id,
            thread_id=normalized.thread_id,
            text=outbound_text,
        )
        return ChannelInboundResponse(
            channel=request.channel,
            event_type=request.event_type,
            run=run,
            command=command,
            outbound_text=outbound_text,
            outbound_delivery=delivery,
            session_key=session_key,
            trace_id=trace_id,
        )

    run_goal = args if command == "run" and args else normalized.text
    run = orchestrator.create_run_from_channel_event(
        normalized.model_copy(update={"text": run_goal}),
        default_repo_path=request.default_repo_path,
    )
    _channel_sessions.attach_run(session_key, run.id)
    outbound_text = format_outbound_run_created(run)
    delivery = _send_outbound(
        channel=normalized.channel,
        channel_id=normalized.channel_id,
        thread_id=normalized.thread_id,
        text=outbound_text,
    )
    return ChannelInboundResponse(
        channel=request.channel,
        event_type=request.event_type,
        run=run,
        command=command or "run",
        outbound_text=outbound_text,
        outbound_delivery=delivery,
        session_key=session_key,
        trace_id=trace_id,
    )


@router.get("/channels/sessions", response_model=list[ChannelSessionSnapshot])
def list_channel_sessions() -> list[ChannelSessionSnapshot]:
    return _channel_sessions.list_snapshots()


@router.get("/channels/metrics", response_model=ChannelMetricsSnapshot)
def get_channel_metrics() -> ChannelMetricsSnapshot:
    return _channel_observability.snapshot()


@router.get("/channels/outbound-retry", response_model=OutboundRetryQueueSnapshot)
def get_outbound_retry_queue() -> OutboundRetryQueueSnapshot:
    return _outbound_retry_queue.snapshot()


@router.get("/channels/approver-allowlist", response_model=ApproverAllowlistResponse)
def get_channel_approver_allowlist() -> ApproverAllowlistResponse:
    return ApproverAllowlistResponse(users=sorted(_command_approver_allowlist))


@router.put("/channels/approver-allowlist", response_model=ApproverAllowlistResponse)
def update_channel_approver_allowlist(
    request: ApproverAllowlistUpdateRequest,
) -> ApproverAllowlistResponse:
    global _command_approver_allowlist
    _command_approver_allowlist = {str(v).strip() for v in request.users if str(v).strip()}
    return ApproverAllowlistResponse(users=sorted(_command_approver_allowlist))


@router.get("/channels/{channel}/trust-policy", response_model=ChannelTrustPolicy)
def get_channel_trust_policy(channel: str) -> ChannelTrustPolicy:
    try:
        return _channel_trust.get_policy(channel)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/channels/{channel}/trust-policy", response_model=ChannelTrustPolicy)
def update_channel_trust_policy(
    channel: str,
    request: ChannelTrustPolicyUpdateRequest,
) -> ChannelTrustPolicy:
    try:
        return _channel_trust.set_policy(
            channel=channel,
            dm_policy=request.dm_policy,
            allow_from=request.allow_from,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/channels/{channel}/pairing/pending", response_model=list[PendingPairingCode])
def list_pending_pairing_codes(channel: str) -> list[PendingPairingCode]:
    try:
        return _channel_trust.list_pending_codes(channel)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/channels/{channel}/pairing/approve", response_model=PairingApprovalResponse)
def approve_pairing_code(
    channel: str,
    request: PairingApprovalRequest,
) -> PairingApprovalResponse:
    try:
        user_id = _channel_trust.approve_pairing_code(channel, request.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PairingApprovalResponse(
        channel=channel.strip().lower(),
        code=request.code.strip().upper(),
        approved=user_id is not None,
        user_id=user_id,
    )


@router.post("/queue", response_model=QueueJobStatusResponse)
def enqueue_run_job(
    request: RunTaskRequest,
) -> QueueJobStatusResponse:
    return _run_queue.enqueue_run(request)


@router.get("/queue/{job_id}", response_model=QueueJobStatusResponse)
def get_run_job_status(job_id: str) -> QueueJobStatusResponse:
    job = _run_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
