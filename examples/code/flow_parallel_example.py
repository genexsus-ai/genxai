"""Example usage of ParallelFlow."""

import asyncio

from genxai import AgentFactory, ParallelFlow


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="a1", role="Analyst", goal="Analyze"),
        AgentFactory.create_agent(id="a2", role="Reviewer", goal="Review"),
    ]

    flow = ParallelFlow(
        agents,
        name="parallel_demo",
        timeout_seconds=60,
        retry_count=2,
        backoff_base=0.5,
        backoff_multiplier=2.0,
        cancel_on_failure=False,
    )
    result = await flow.run({"topic": "Parallel insights"})
    print("ParallelFlow result keys:", list(result.keys()))


if __name__ == "__main__":
    asyncio.run(main())