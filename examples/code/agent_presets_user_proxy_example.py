"""Example usage of AssistantAgent and UserProxyAgent presets."""

import asyncio

from genxai import AssistantAgent, UserProxyAgent, Tool, ToolCategory, ToolMetadata, ToolParameter, ToolRegistry, AgentRuntime


class HumanInputTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            metadata=ToolMetadata(
                name="human_input",
                description="Collects human input from the console",
                category=ToolCategory.CUSTOM,
            ),
            parameters=[ToolParameter(name="prompt", type="string", description="Prompt")],
        )

    async def _execute(self, **kwargs):
        prompt = kwargs.get("prompt", "Your response:")
        return {"response": input(f"{prompt} ")}


async def main() -> None:
    ToolRegistry.register(HumanInputTool())

    assistant = AssistantAgent.create(
        id="assistant",
        goal="Help the user",
        tools=[],
    )
    user_proxy = UserProxyAgent.create(
        id="user_proxy",
        tools=["human_input"],
    )

    user_runtime = AgentRuntime(agent=user_proxy)
    assistant_runtime = AgentRuntime(agent=assistant)

    user_reply = await user_runtime.execute(
        task="Ask the user for requirements",
        context={"prompt": "What do you need?"},
    )
    response = await assistant_runtime.execute(
        task="Answer the user",
        context={"user_input": user_reply},
    )
    print(response.get("output"))


if __name__ == "__main__":
    asyncio.run(main())