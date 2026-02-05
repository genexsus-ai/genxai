"""Demonstrate schema-based tool calling with OpenAI."""

import asyncio
import os

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - auto-register tools


async def main() -> None:
    agent = AgentFactory.create_agent(
        id="tool_agent",
        role="Math Helper",
        goal="Use tools when needed",
        tools=["calculator"],
        llm_model="gpt-4",
    )

    runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
    tools = {tool.metadata.name: tool for tool in ToolRegistry.list_all()}
    runtime.set_tools(tools)

    result = await runtime.execute(task="Calculate 42 * 7 using the calculator tool.")
    print(result["output"])


if __name__ == "__main__":
    asyncio.run(main())