"""Shared typed artifact schema used across GenXAI applications.

This module defines discriminated payload types for common artifact outputs
such as diffs, command execution output, plan summaries, and diagnostics.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class DiffArtifactPayload(BaseModel):
    """Structured representation of a file edit or patch result."""

    type: Literal["diff"] = "diff"
    file_path: Optional[str] = None
    before: str = ""
    after: str = ""
    patch: Optional[str] = None


class CommandOutputArtifactPayload(BaseModel):
    """Structured representation of command execution output."""

    type: Literal["command_output"] = "command_output"
    command: str
    argv: list[str] = Field(default_factory=list)
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class PlanSummaryArtifactPayload(BaseModel):
    """Structured plan summary artifact."""

    type: Literal["plan_summary"] = "plan_summary"
    steps: list[str] = Field(default_factory=list)
    objective: Optional[str] = None
    notes: Optional[str] = None


class DiagnosticsArtifactPayload(BaseModel):
    """Structured diagnostics artifact for warnings/errors/info."""

    type: Literal["diagnostics"] = "diagnostics"
    level: Literal["info", "warning", "error"] = "info"
    code: Optional[str] = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SummaryArtifactPayload(BaseModel):
    """General plain-text summary artifact payload."""

    type: Literal["summary"] = "summary"
    text: str


ArtifactPayload = Union[
    DiffArtifactPayload,
    CommandOutputArtifactPayload,
    PlanSummaryArtifactPayload,
    DiagnosticsArtifactPayload,
    SummaryArtifactPayload,
]


ArtifactKind = Literal[
    "plan",
    "plan_summary",
    "diff",
    "command_output",
    "summary",
    "diagnostics",
]


class Artifact(BaseModel):
    """Framework-wide artifact envelope with discriminated payload."""

    id: str = Field(default_factory=lambda: f"artifact_{uuid4().hex[:8]}")
    kind: ArtifactKind
    title: str
    content: str = ""
    payload: Optional[ArtifactPayload] = Field(default=None, discriminator="type")


__all__ = [
    "Artifact",
    "ArtifactKind",
    "ArtifactPayload",
    "CommandOutputArtifactPayload",
    "DiagnosticsArtifactPayload",
    "DiffArtifactPayload",
    "PlanSummaryArtifactPayload",
    "SummaryArtifactPayload",
]
