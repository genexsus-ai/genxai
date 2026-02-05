"""Agent using tools + memory system in the runtime."""

import asyncio
import os
from pathlib import Path

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.memory.manager import MemorySystem
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - auto-register


async def main() -> None:
    agent = AgentFactory.create_agent(
        id="assistant",
        role="Personal Assistant",
        goal="Remember preferences and use tools",
        tools=["calculator"],
        llm_model="gpt-3.5-turbo",
        enable_memory=True,
    )

    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    tools = {tool.metadata.name: tool for tool in ToolRegistry.list_all()}
    runtime.set_tools(tools)

    memory = MemorySystem(
        agent_id="assistant",
        persistence_enabled=True,
        persistence_path=Path(".genxai/memory"),
    )
    runtime.set_memory(memory)

    await runtime.execute(task="My name is Sam and I like TypeScript.")
    result = await runtime.execute(task="What is 12 * 9 and what is my name?")
    print(result["output"])


if __name__ == "__main__":
    asyncio.run(main())