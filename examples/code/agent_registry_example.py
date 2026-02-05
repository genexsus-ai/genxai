"""Demonstrate AgentRegistry usage for managing agent instances."""

import asyncio
import os

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.agent.runtime import AgentRuntime


async def main() -> None:
    agent = AgentFactory.create_agent(
        id="registry_agent",
        role="Registry Demo",
        goal="Show how AgentRegistry works",
        llm_model="gpt-3.5-turbo",
    )

    AgentRegistry.register(agent)
    print("Registered agents:", AgentRegistry.list_all())

    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    result = await runtime.execute(task="Say hello in one short sentence.")
    print("Response:", result["output"])


if __name__ == "__main__":
    asyncio.run(main())