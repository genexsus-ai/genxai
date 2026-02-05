"""Example usage of RouterFlow."""

import asyncio

from genxai import AgentFactory, RouterFlow


def router(state):
    return "planner" if state.get("route") == "plan" else "executor"


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="planner", role="Planner", goal="Plan"),
        AgentFactory.create_agent(id="executor", role="Executor", goal="Execute"),
    ]

    flow = RouterFlow(
        agents,
        router=router,
        timeout_seconds=75,
        retry_count=2,
        backoff_base=1.0,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"route": "plan"})
    print("RouterFlow nodes:", result.get("node_results", {}).keys())


if __name__ == "__main__":
    asyncio.run(main())