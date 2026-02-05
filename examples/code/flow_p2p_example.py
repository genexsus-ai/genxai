"""Example usage of P2PFlow."""

import asyncio

from genxai import AgentFactory, P2PFlow


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="peer_1", role="Analyst", goal="Contribute"),
        AgentFactory.create_agent(id="peer_2", role="Reviewer", goal="Review"),
        AgentFactory.create_agent(id="peer_3", role="Engineer", goal="Build"),
    ]

    flow = P2PFlow(
        agents,
        max_rounds=4,
        consensus_threshold=0.7,
        convergence_window=2,
        quality_threshold=0.8,
    )
    result = await flow.run({"topic": "Decentralized orchestration"})
    print("P2PFlow termination:", result.get("termination_reason"))


if __name__ == "__main__":
    asyncio.run(main())