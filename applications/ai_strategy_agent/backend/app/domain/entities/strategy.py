"""Domain entities for AI strategy brainstorming."""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class BusinessObjective:
    """Represents a business objective input."""

    description: str


@dataclass(frozen=True)
class StrategicTheme:
    """High-level strategic theme."""

    title: str
    rationale: str


@dataclass(frozen=True)
class Initiative:
    """Concrete AI initiative proposal."""

    name: str
    rationale: str
    owner: str
    timeline: str
    dependencies: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RoadmapItem:
    """Prioritized roadmap item."""

    horizon: str
    initiative: str
    outcomes: List[str]


@dataclass(frozen=True)
class Risk:
    """Risk and mitigation."""

    risk: str
    mitigation: str


@dataclass(frozen=True)
class KPI:
    """Key performance indicator."""

    name: str
    target: str
    measurement: str