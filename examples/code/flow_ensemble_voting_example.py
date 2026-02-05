"""Example usage of EnsembleVotingFlow."""

import asyncio

from genxai import AgentFactory, EnsembleVotingFlow


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="a1", role="Analyst", goal="Answer"),
        AgentFactory.create_agent(id="a2", role="Reviewer", goal="Answer"),
    ]

    flow = EnsembleVotingFlow(
        agents,
        timeout_seconds=65,
        retry_count=2,
        backoff_base=0.5,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"question": "Best architecture?"})
    print("Ensemble winner:", result.get("winner"))


if __name__ == "__main__":
    asyncio.run(main())