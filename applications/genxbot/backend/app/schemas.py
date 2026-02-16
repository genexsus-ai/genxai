"""Pydantic schemas for GenXBot autonomous coding workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunTaskRequest(BaseModel):
    goal: str = Field(..., min_length=3)
    repo_path: str = Field(..., min_length=1)
    context: Optional[str] = None


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: f"step_{uuid4().hex[:8]}")
    title: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    requires_approval: bool = False


class TimelineEvent(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    agent: str
    event: str
    content: str


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: f"artifact_{uuid4().hex[:8]}")
    kind: Literal["plan", "diff", "command_output", "summary"]
    title: str
    content: str


class ProposedAction(BaseModel):
    id: str = Field(default_factory=lambda: f"action_{uuid4().hex[:8]}")
    action_type: Literal["edit", "command"]
    description: str
    safe: bool = False
    status: Literal["pending", "approved", "rejected", "executed"] = "pending"
    command: Optional[str] = None
    file_path: Optional[str] = None
    patch: Optional[str] = None


class RunSession(BaseModel):
    id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:10]}")
    goal: str
    repo_path: str
    status: Literal["created", "awaiting_approval", "running", "completed", "failed"] = "created"
    plan_steps: list[PlanStep] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    pending_actions: list[ProposedAction] = Field(default_factory=list)
    memory_summary: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class ApprovalRequest(BaseModel):
    action_id: str
    approve: bool
    comment: Optional[str] = None
