"""Termination policies (GoF Strategy pattern)."""

from abc import ABC, abstractmethod
from datetime import datetime


class TerminationPolicy(ABC):
    """Abstract termination policy interface."""

    @abstractmethod
    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        """Return (should_terminate, reason)."""


class CompositeTerminationPolicy(TerminationPolicy):
    """Compose multiple termination policies."""

    def __init__(self, policies: list[TerminationPolicy]) -> None:
        self._policies = policies

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        for policy in self._policies:
            should_stop, reason = policy.should_terminate(state)
            if should_stop:
                return True, reason
        return False, None


class MaxRoundsTerminationPolicy(TerminationPolicy):
    """Terminate after max rounds."""

    def __init__(self, max_rounds: int) -> None:
        self._max_rounds = max_rounds

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        if state.get("round", 0) >= self._max_rounds:
            return True, f"Max rounds reached ({self._max_rounds})"
        return False, None


class TimeoutTerminationPolicy(TerminationPolicy):
    """Terminate when elapsed seconds exceed timeout."""

    def __init__(self, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds
        self._start_time = datetime.now()

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        elapsed = (datetime.now() - self._start_time).total_seconds()
        if elapsed >= self._timeout_seconds:
            return True, f"Timeout reached ({self._timeout_seconds}s)"
        return False, None


class QualityTerminationPolicy(TerminationPolicy):
    """Terminate when quality threshold met."""

    def __init__(self, quality_threshold: float) -> None:
        self._quality_threshold = quality_threshold

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        if state.get("quality_score", 0.0) >= self._quality_threshold:
            return True, "Quality threshold met"
        return False, None


class ConvergenceTerminationPolicy(TerminationPolicy):
    """Terminate when conversation converges."""

    def __init__(self, window: int = 2) -> None:
        self._window = window

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        history = state.get("message_history", [])
        if len(history) < self._window:
            return False, None
        last_messages = history[-self._window :]
        unique = {item.get("content", "")[:80] for item in last_messages}
        if len(unique) <= 1:
            return True, "Conversation converged"
        return False, None


class ConsensusTerminationPolicy(TerminationPolicy):
    """Terminate when consensus score threshold met."""

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def should_terminate(self, state: dict) -> tuple[bool, str | None]:
        if state.get("consensus_score", 0.0) >= self._threshold:
            return True, "Consensus threshold met"
        return False, None