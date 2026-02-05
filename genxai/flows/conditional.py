"""Conditional flow orchestrator."""

from typing import Callable, List

from genxai.core.graph.engine import Graph
from genxai.core.graph.edges import Edge
from genxai.core.graph.nodes import AgentNode, InputNode, OutputNode
from genxai.flows.base import FlowOrchestrator


class ConditionalFlow(FlowOrchestrator):
    """Route to a single agent based on a condition function."""

    def __init__(
        self,
        agents: List,
        condition: Callable[[dict], str],
        name: str = "conditional_flow",
        llm_provider=None,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)
        self.condition = condition

    def build_graph(self) -> Graph:
        graph = Graph(name=self.name)
        start = InputNode(id="input")
        graph.add_node(start)

        end = OutputNode(id="output")
        graph.add_node(end)
        nodes = self._agent_nodes()
        for node in nodes:
            graph.add_node(node)
            graph.add_edge(
                Edge(
                    source=start.id,
                    target=node.id,
                    condition=lambda state, agent_id=node.id: self.condition(state) == agent_id,
                )
            )
            graph.add_edge(Edge(source=node.id, target=end.id))

        graph.add_edge(Edge(source=start.id, target=end.id))

        return graph