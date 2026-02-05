"""Example usage of LoopFlow."""

import asyncio

from genxai import AgentFactory, LoopFlow


async def main() -> None:
    agents = [AgentFactory.create_agent(id="loop_agent", role="Loop", goal="Iterate")]

    flow = LoopFlow(
        agents,
        condition_key="done",
        max_iterations=3,
        timeout_seconds=45,
        retry_count=2,
        backoff_base=0.5,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"done": False})
    print("LoopFlow state keys:", list(result.keys()))


if __name__ == "__main__":
    asyncio.run(main())