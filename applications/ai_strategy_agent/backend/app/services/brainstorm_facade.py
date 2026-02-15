"""Facade for strategy brainstorming orchestration."""

from __future__ import annotations

from app.application.services.brainstorm_service import BrainstormService, build_engine_factory
from app.domain.policies.consensus import ThresholdConsensusPolicy
from app.domain.policies.termination import (
    CompositeTerminationPolicy,
    ConvergenceTerminationPolicy,
    ConsensusTerminationPolicy,
    MaxRoundsTerminationPolicy,
    QualityTerminationPolicy,
    TimeoutTerminationPolicy,
)
from app.infra.metrics.metrics_adapter import MetricsRecorderAdapter
from app.infra.repositories.in_memory import InMemoryStrategyRepository
from app.services.peer_config import build_peer_agents


def build_brainstorm_service(
    max_rounds: int,
    consensus_threshold: float,
    convergence_window: int,
    quality_threshold: float,
    openai_api_key: str | None = None,
):
    peers = build_peer_agents()
    consensus_policy = ThresholdConsensusPolicy(consensus_threshold)
    termination_policy = CompositeTerminationPolicy(
        [
            MaxRoundsTerminationPolicy(max_rounds),
            ConvergenceTerminationPolicy(convergence_window),
            QualityTerminationPolicy(quality_threshold),
            ConsensusTerminationPolicy(consensus_threshold),
            TimeoutTerminationPolicy(90),
        ]
    )
    engine_factory = build_engine_factory(
        peers=peers,
        consensus_policy=consensus_policy,
        termination_policy=termination_policy,
        llm_provider=None,
        openai_api_key=openai_api_key,
    )
    repository = InMemoryStrategyRepository()
    metrics = MetricsRecorderAdapter()
    return BrainstormService(engine_factory=engine_factory, repository=repository, metrics=metrics)