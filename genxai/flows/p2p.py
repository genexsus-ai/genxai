"""Peer-to-peer flow orchestrator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from genxai.core.agent.runtime import AgentRuntime
from genxai.flows.base import FlowOrchestrator


class P2PFlow(FlowOrchestrator):
    """Run a peer-to-peer agent loop with lightweight consensus stopping.

    This flow doesn't use the graph engine for routing; it mirrors the
    P2P pattern where agents communicate directly and decide when to stop.
    """

    def __init__(
        self,
        agents: List[Any],
        name: str = "p2p_flow",
        llm_provider: Any = None,
        max_rounds: int = 5,
        timeout_seconds: float = 300,
        consensus_threshold: float = 0.6,
        convergence_window: int = 3,
        quality_threshold: float = 0.85,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)
        self.max_rounds = max_rounds
        self.timeout_seconds = timeout_seconds
        self.consensus_threshold = consensus_threshold
        self.convergence_window = convergence_window
        self.quality_threshold = quality_threshold
        self._start_time = datetime.now()

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        if state is None:
            state = {}

        state["input"] = input_data
        state.setdefault("messages", [])
        state.setdefault("solution_quality", 0.0)
        state.setdefault("goal_achieved", False)

        runtimes = {
            agent.id: AgentRuntime(agent=agent, llm_provider=self.llm_provider)
            for agent in self.agents
        }

        for round_idx in range(self.max_rounds):
            for agent in self.agents:
                result = await runtimes[agent.id].execute(
                    task=state.get("task", "Collaborate with peers"),
                    context=state,
                )
                state["messages"].append({
                    "round": round_idx + 1,
                    "agent_id": agent.id,
                    "result": result,
                })

            state["solution_quality"] = self._estimate_quality(state)
            if state["solution_quality"] >= self.quality_threshold:
                state["goal_achieved"] = True

            should_stop, reason = self._should_terminate(state, round_idx + 1)
            if should_stop:
                state["termination_reason"] = reason
                break

            if state.get("iterations", 0) >= max_iterations:
                state["termination_reason"] = "Max iterations reached"
                break

        return state

    def _should_terminate(self, state: Dict[str, Any], iteration: int) -> tuple[bool, Optional[str]]:
        if iteration >= self.max_rounds:
            return True, f"Max rounds reached ({self.max_rounds})"

        elapsed = (datetime.now() - self._start_time).total_seconds()
        if elapsed >= self.timeout_seconds:
            return True, f"Timeout reached ({self.timeout_seconds}s)"

        if state.get("goal_achieved"):
            return True, "Goal achieved"

        if self._consensus_reached(state):
            return True, "Consensus to terminate"

        if self._detect_convergence(state):
            return True, "Conversation converged"

        if self._detect_deadlock(state):
            return True, "Deadlock detected"

        return False, None

    def _consensus_reached(self, state: Dict[str, Any]) -> bool:
        messages = state.get("messages", [])
        if not messages:
            return False
        votes = 0
        for msg in messages[-len(self.agents):]:
            result = msg.get("result", {})
            if isinstance(result, dict) and str(result.get("status", "")).lower() == "completed":
                votes += 1
        return (votes / max(1, len(self.agents))) >= self.consensus_threshold

    def _detect_convergence(self, state: Dict[str, Any]) -> bool:
        messages = state.get("messages", [])
        if len(messages) < self.convergence_window:
            return False

        recent = messages[-self.convergence_window:]
        summaries = set(
            str(msg.get("result", {}).get("output", ""))[:100] for msg in recent
        )
        return len(summaries) <= 2

    def _detect_deadlock(self, state: Dict[str, Any]) -> bool:
        messages = state.get("messages", [])
        if len(messages) < 6:
            return False
        recent = messages[-6:]
        senders = [msg.get("agent_id", "") for msg in recent]
        return len(senders) >= 6 and senders[:3] == senders[3:6]

    def _estimate_quality(self, state: Dict[str, Any]) -> float:
        messages = state.get("messages", [])
        if not messages:
            return 0.0
        recent = messages[-len(self.agents):]
        scores = []
        for msg in recent:
            result = msg.get("result", {})
            output = result.get("output") if isinstance(result, dict) else ""
            scores.append(min(1.0, len(str(output)) / 500))
        return sum(scores) / max(1, len(scores))