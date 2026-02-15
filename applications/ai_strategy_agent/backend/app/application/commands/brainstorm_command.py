"""Command DTOs for brainstorming."""

from pydantic import BaseModel, Field


class BrainstormRequest(BaseModel):
    company_name: str = Field(..., min_length=2)
    objectives: list[str]
    constraints: list[str] = []
    horizon: str = "12 months"
    risk_posture: str = "balanced"


class BrainstormResponse(BaseModel):
    executive_summary: str
    strategic_themes: list[dict]
    ai_initiatives: list[dict]
    prioritized_roadmap: list[dict]
    risks_and_mitigations: list[dict]
    kpis: list[dict]
    termination_reason: str
    rounds: int
    quality_score: float
    consensus_score: float