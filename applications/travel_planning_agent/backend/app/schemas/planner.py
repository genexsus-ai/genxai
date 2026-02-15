from pydantic import BaseModel, Field


class TravelPreferences(BaseModel):
    origin: str
    destination: str
    start_date: str
    end_date: str
    travelers: int = Field(1, ge=1, le=10)
    budget: float = Field(..., ge=0)
    interests: list[str] = Field(default_factory=list)


class PlanRequest(BaseModel):
    session_title: str = Field(..., min_length=3, max_length=200)
    preferences: TravelPreferences


class PlanResponse(BaseModel):
    session_id: int
    plan_id: int
    coordinator: dict
    delegator: dict
    itinerary: dict
    budget_breakdown: dict
    recommendations: dict
    summary: str
    workflow: dict


class StreamEvent(BaseModel):
    event: str
    data: dict
