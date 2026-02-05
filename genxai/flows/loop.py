"""Loop flow orchestrator."""

from typing import List

from genxai.core.graph.engine import Graph
from genxai.core.graph.edges import Edge
from genxai.core.graph.nodes import AgentNode, InputNode, LoopNode, OutputNode
from genxai.flows.base import FlowOrchestrator


class LoopFlow(FlowOrchestrator):
    """Execute an agent inside a loop with a termination condition."""

    def __init__(
        self,
        agents: List,
        condition_key: str,
        max_iterations: int = 5,
        name: str = "loop_flow",
        llm_provider=None,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)
        self.condition_key = condition_key
        self.loop_iterations = max_iterations

    def build_graph(self) -> Graph:
        graph = Graph(name=self.name)
        start = InputNode(id="input")
        loop = LoopNode(id="loop", condition=self.condition_key, max_iterations=self.loop_iterations)
        agent = self._agent_nodes()[0]
        end = OutputNode(id="output")

        graph.add_node(start)
        graph.add_node(loop)
        graph.add_node(agent)
        graph.add_node(end)

        graph.add_edge(Edge(source=start.id, target=loop.id))
        graph.add_edge(Edge(source=loop.id, target=agent.id))
        graph.add_edge(Edge(source=agent.id, target=end.id))

        return graph