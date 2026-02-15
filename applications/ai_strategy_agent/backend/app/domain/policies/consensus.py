"""Consensus policy strategies (GoF Strategy pattern)."""

from abc import ABC, abstractmethod


class ConsensusPolicy(ABC):
    """Policy interface for consensus determination."""

    @abstractmethod
    def consensus_reached(self, votes: list[bool]) -> bool:
        """Return True if consensus reached."""


class ThresholdConsensusPolicy(ConsensusPolicy):
    """Consensus when ratio of True votes exceeds threshold."""

    def __init__(self, threshold: float) -> None:
        self._threshold = threshold

    def consensus_reached(self, votes: list[bool]) -> bool:
        if not votes:
            return False
        true_votes = sum(1 for vote in votes if vote)
        return true_votes / len(votes) >= self._threshold