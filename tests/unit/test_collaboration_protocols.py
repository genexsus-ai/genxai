"""Unit tests for collaboration protocols."""

import pytest

from genxai.core.communication.collaboration import (
    VotingProtocol,
    NegotiationProtocol,
    AuctionProtocol,
)


@pytest.mark.asyncio
async def test_voting_protocol():
    protocol = VotingProtocol()
    result = await protocol.run(["a", "b", "a"], {})
    assert result.winner == "a"


@pytest.mark.asyncio
async def test_negotiation_protocol():
    protocol = NegotiationProtocol()
    assert await protocol.run(["x", "x"], {}) == "x"
    assert await protocol.run(["x", "y"], {"fallback": "z"}) == "z"


@pytest.mark.asyncio
async def test_auction_protocol():
    protocol = AuctionProtocol()
    assert await protocol.run([1, 5, 3], {}) == 5