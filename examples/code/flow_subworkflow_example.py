"""Example usage of SubworkflowFlow."""

import asyncio

from genxai import AgentFactory, Graph, SubworkflowFlow
from genxai.core.graph.nodes import AgentNode, InputNode, OutputNode
from genxai.core.graph.edges import Edge


async def main() -> None:
    agent = AgentFactory.create_agent(id="sub_agent", role="Agent", goal="Respond")

    graph = Graph(name="subgraph")
    graph.add_node(InputNode(id="input"))
    graph.add_node(AgentNode(id="sub_agent", agent_id=agent.id))
    graph.add_node(OutputNode(id="output"))
    graph.add_edge(Edge(source="input", target="sub_agent"))
    graph.add_edge(Edge(source="sub_agent", target="output"))

    flow = SubworkflowFlow(
        graph,
        timeout_seconds=30,
        retry_count=1,
        backoff_base=0.5,
        backoff_multiplier=2.0,
        cancel_on_failure=True,
    )
    result = await flow.run({"topic": "Subworkflow"})
    print("SubworkflowFlow keys:", list(result.keys()))


if __name__ == "__main__":
    asyncio.run(main())