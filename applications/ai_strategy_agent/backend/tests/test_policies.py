from app.domain.policies.consensus import ThresholdConsensusPolicy
from app.domain.policies.termination import (
    CompositeTerminationPolicy,
    ConsensusTerminationPolicy,
    MaxRoundsTerminationPolicy,
)


def test_threshold_consensus_policy():
    policy = ThresholdConsensusPolicy(0.6)
    assert policy.consensus_reached([True, False, True])
    assert not policy.consensus_reached([False, False, True])


def test_termination_policies():
    composite = CompositeTerminationPolicy(
        [MaxRoundsTerminationPolicy(2), ConsensusTerminationPolicy(0.7)]
    )
    should_stop, reason = composite.should_terminate({"round": 2, "consensus_score": 0.1})
    assert should_stop
    assert "Max rounds" in reason
