"""Example usage of CoordinatorWorkerFlow."""

import asyncio

from genxai import AgentFactory, CoordinatorWorkerFlow


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="coordinator", role="Coordinator", goal="Plan"),
        AgentFactory.create_agent(id="worker1", role="Worker", goal="Execute"),
        AgentFactory.create_agent(id="worker2", role="Worker", goal="Execute"),
    ]

    flow = CoordinatorWorkerFlow(
        agents,
        timeout_seconds=90,
        retry_count=2,
        backoff_base=1.0,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"task": "Ship release"})
    print("Worker results:", len(result.get("worker_results", [])))


if __name__ == "__main__":
    asyncio.run(main())