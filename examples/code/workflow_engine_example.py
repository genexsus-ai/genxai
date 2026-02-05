"""Demonstrate the WorkflowEngine compatibility wrapper."""

import asyncio

from genxai.core.graph.engine import WorkflowEngine
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge


async def main() -> None:
    engine = WorkflowEngine(name="compat_workflow")
    engine.add_node(InputNode())
    engine.add_node(AgentNode(id="planner", agent_id="planner_agent"))
    engine.add_node(OutputNode())

    engine.add_edge(Edge(source="input", target="planner"))
    engine.add_edge(Edge(source="planner", target="output"))

    result = await engine.execute(
        start_node="input",
        input_data={"task": "Draft a short meeting agenda."},
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())