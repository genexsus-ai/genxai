"""Application service orchestrating brainstorming workflows."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any

from app.application.commands.brainstorm_command import BrainstormRequest
from app.domain.policies.consensus import ConsensusPolicy
from app.domain.policies.termination import TerminationPolicy
from app.domain.services.p2p_engine import P2PStrategyEngine, StrategyMessageBus


class StrategyRepository:
    """Repository interface (Repository pattern)."""

    def save(self, session: dict[str, Any]) -> None:
        raise NotImplementedError

    def get(self, session_id: str) -> dict[str, Any] | None:
        raise NotImplementedError


class MetricsRecorder:
    """Metrics recorder interface (Adapter pattern)."""

    def record(self, workflow_name: str, duration: float, status: str) -> None:
        raise NotImplementedError


logger = logging.getLogger(__name__)


@dataclass
class BrainstormService:
    """Application service (Facade pattern)."""

    engine_factory: callable
    repository: StrategyRepository
    metrics: MetricsRecorder

    async def run(self, request: BrainstormRequest, on_message=None) -> dict[str, Any]:
        start_time = time.time()
        logger.info(
            "Brainstorm start: company=%s horizon=%s risk_posture=%s",
            request.company_name,
            request.horizon,
            request.risk_posture,
        )
        engine: P2PStrategyEngine = self.engine_factory(on_message)

        context = {
            "company_name": request.company_name,
            "objectives": request.objectives,
            "constraints": request.constraints,
            "horizon": request.horizon,
            "risk_posture": request.risk_posture,
        }

        logger.info("Brainstorm workflow run started")
        result = await engine.run(context)
        logger.info("Brainstorm workflow run complete")
        session = {"request": context, "result": result}
        self.repository.save(session)
        self.metrics.record("ai_strategy_brainstorm", time.time() - start_time, "success")
        logger.info(
            "Brainstorm completed: rounds=%s quality_score=%s consensus_score=%s",
            result.get("round"),
            result.get("quality_score"),
            result.get("consensus_score"),
        )
        return result


def build_engine_factory(
    peers: list[dict[str, str]],
    consensus_policy: ConsensusPolicy,
    termination_policy: TerminationPolicy,
    llm_provider: Any | None,
    openai_api_key: str | None,
):
    def factory(on_message=None) -> P2PStrategyEngine:
        message_bus = StrategyMessageBus()
        if on_message:
            message_bus.subscribe(on_message)
        return P2PStrategyEngine(
            peers=peers,
            consensus_policy=consensus_policy,
            termination_policy=termination_policy,
            message_bus=message_bus,
            llm_provider=llm_provider,
            openai_api_key=openai_api_key,
        )

    return factory