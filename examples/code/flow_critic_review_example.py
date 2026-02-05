"""Example usage of CriticReviewFlow."""

import asyncio

from genxai import AgentFactory, CriticReviewFlow


async def main() -> None:
    agents = [
        AgentFactory.create_agent(id="writer", role="Writer", goal="Draft"),
        AgentFactory.create_agent(id="critic", role="Critic", goal="Review"),
    ]

    flow = CriticReviewFlow(
        agents,
        max_iterations=2,
        timeout_seconds=90,
        retry_count=2,
        backoff_base=1.0,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"topic": "Product launch"})
    print("CriticReviewFlow drafts:", len(result.get("drafts", [])))


if __name__ == "__main__":
    asyncio.run(main())