"""API schemas for strategy brainstorming."""

from pydantic import BaseModel


class BrainstormRequestSchema(BaseModel):
    company_name: str
    objectives: list[str]
    constraints: list[str] = []
    horizon: str = "12 months"
    risk_posture: str = "balanced"


class BrainstormResponseSchema(BaseModel):
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