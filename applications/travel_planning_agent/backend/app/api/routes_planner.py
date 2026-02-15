import asyncio
import json
from datetime import datetime, UTC
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.planner import PlanRequest, PlanResponse
from app.security.dependencies import get_current_user
from app.services.planner_service import create_plan


router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/plan", response_model=PlanResponse)
async def plan_trip(
    payload: PlanRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> PlanResponse:
    return await create_plan(db, user, payload.model_dump())


@router.post("/plan/stream")
async def plan_trip_stream(
    payload: PlanRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> StreamingResponse:
    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[dict] = asyncio.Queue()

        async def callback(event: dict) -> None:
            payload = event if isinstance(event, dict) else {"message": str(event)}
            node_id = payload.get("node_id") or payload.get("node") or payload.get("id")
            event_type = payload.get("event") or payload.get("type") or "node_event"
            status = payload.get("status") or payload.get("state")
            message = payload.get("message") or payload.get("detail")
            if not message and status and node_id:
                message = f"{node_id} {status}"
            raw_output = payload.get("output")
            if isinstance(raw_output, str):
                text_output = raw_output
            elif raw_output is not None:
                text_output = json.dumps(raw_output, ensure_ascii=False)
            else:
                text_output = message or ""
            await queue.put(
                {
                    "event": "node",
                    "data": {
                        "node_id": node_id,
                        "event": event_type,
                        "status": status,
                        "message": message,
                        "output": payload.get("output"),
                        "text_output": text_output,
                        "timestamp": payload.get("timestamp")
                        or datetime.now(UTC).isoformat(),
                    },
                }
            )

        async def run_plan() -> None:
            try:
                result = await create_plan(
                    db,
                    user,
                    payload.model_dump(),
                    event_callback=callback,
                )
                await queue.put({"event": "complete", "data": result})
            except Exception as exc:
                await queue.put({
                    "event": "error",
                    "data": {"message": str(exc)},
                })

        task = asyncio.create_task(run_plan())
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event") in {"complete", "error"}:
                    break
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
