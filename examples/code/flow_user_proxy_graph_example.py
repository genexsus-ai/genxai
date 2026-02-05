"""Workflow example that mimics a UserProxy agent via a ToolNode step."""

import asyncio

from genxai import AgentFactory, Graph
from genxai.core.graph.edges import Edge
from genxai.core.graph.nodes import InputNode, OutputNode, ToolNode, AgentNode
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory
from genxai.tools.registry import ToolRegistry


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

    assistant = AgentFactory.create_agent(
        id="assistant",
        role="Assistant",
        goal="Help the user",
        tools=[],
    )

    graph = Graph(name="user_proxy_flow")
    graph.add_node(InputNode(id="input"))
    graph.add_node(
        ToolNode(
            id="user_input",
            tool_name="human_input",
            tool_params={"prompt": "What do you need?"},
        )
    )
    graph.add_node(AgentNode(id="assistant_node", agent_id=assistant.id))
    graph.add_node(OutputNode(id="output"))

    graph.add_edge(Edge(source="input", target="user_input"))
    graph.add_edge(Edge(source="user_input", target="assistant_node"))
    graph.add_edge(Edge(source="assistant_node", target="output"))

    result = await graph.run(input_data={})
    print("Workflow output:", result.get("output"))


if __name__ == "__main__":
    asyncio.run(main())