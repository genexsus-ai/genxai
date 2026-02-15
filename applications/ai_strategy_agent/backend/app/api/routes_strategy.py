"""Strategy brainstorming API routes."""

import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.application.commands.brainstorm_command import BrainstormRequest
from app.config import get_settings
from app.observability.metrics import export_metrics
from app.schemas.brainstorm import BrainstormRequestSchema, BrainstormResponseSchema
from app.services.brainstorm_facade import build_brainstorm_service

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])
logger = logging.getLogger(__name__)


@router.post("/brainstorm", response_model=BrainstormResponseSchema)
async def brainstorm(request: BrainstormRequestSchema) -> BrainstormResponseSchema:
    settings = get_settings()
    logger.info(
        "Brainstorm request received: company=%s horizon=%s risk_posture=%s",
        request.company_name,
        request.horizon,
        request.risk_posture,
    )
    service = build_brainstorm_service(
        max_rounds=settings.max_rounds,
        consensus_threshold=settings.consensus_threshold,
        convergence_window=settings.convergence_window,
        quality_threshold=settings.quality_threshold,
        openai_api_key=settings.openai_api_key,
    )
    result = await service.run(BrainstormRequest(**request.model_dump()))
    artifact = result.get("strategy_artifact", {})
    logger.info(
        "Brainstorm response ready: rounds=%s quality_score=%s consensus_score=%s",
        result.get("round"),
        result.get("quality_score"),
        result.get("consensus_score"),
    )
    return BrainstormResponseSchema(
        executive_summary=artifact.get("executive_summary", ""),
        strategic_themes=artifact.get("strategic_themes", []),
        ai_initiatives=artifact.get("ai_initiatives", []),
        prioritized_roadmap=artifact.get("prioritized_roadmap", []),
        risks_and_mitigations=artifact.get("risks_and_mitigations", []),
        kpis=artifact.get("kpis", []),
        termination_reason=result.get("termination_reason", "completed"),
        rounds=result.get("round", 0),
        quality_score=result.get("quality_score", 0.0),
        consensus_score=result.get("consensus_score", 0.0),
    )


@router.api_route("/brainstorm/stream", methods=["POST", "GET"])
async def brainstorm_stream(request: BrainstormRequestSchema):
    settings = get_settings()
    logger.info(
        "Brainstorm stream started: company=%s horizon=%s risk_posture=%s",
        request.company_name,
        request.horizon,
        request.risk_posture,
    )

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def on_message(message):
            await queue.put(message)

        service = build_brainstorm_service(
            max_rounds=settings.max_rounds,
            consensus_threshold=settings.consensus_threshold,
            convergence_window=settings.convergence_window,
            quality_threshold=settings.quality_threshold,
            openai_api_key=settings.openai_api_key,
        )

        task = asyncio.create_task(
            service.run(BrainstormRequest(**request.model_dump()), on_message=on_message)
        )

        while True:
            if task.done() and queue.empty():
                result = await task
                artifact = result.get("strategy_artifact", {})
                done_payload = {
                    "event": "done",
                    "termination_reason": result.get("termination_reason", ""),
                    "strategy_artifact": artifact,
                    "ranked_use_cases": artifact.get("ai_initiatives", []),
                }
                logger.info(
                    "Brainstorm stream complete: rounds=%s quality_score=%s consensus_score=%s",
                    result.get("round"),
                    result.get("quality_score"),
                    result.get("consensus_score"),
                )
                yield f"data: {json.dumps(done_payload)}\n\n"
                break

            try:
                message = await asyncio.wait_for(queue.get(), timeout=0.5)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                continue

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/metrics")
async def metrics():
    return export_metrics()