"""Parallel flow orchestrator."""

from typing import List

from genxai.core.graph.engine import Graph
from genxai.core.graph.edges import Edge, ParallelEdge
from genxai.core.graph.nodes import AgentNode, InputNode, OutputNode
from genxai.flows.base import FlowOrchestrator


class ParallelFlow(FlowOrchestrator):
    """Execute all agents in parallel from a shared input node."""

    def build_graph(self) -> Graph:
        graph = Graph(name=self.name)
        start = InputNode(id="input")
        end = OutputNode(id="output")
        graph.add_node(start)
        graph.add_node(end)

        nodes: List[AgentNode] = self._agent_nodes()
        for node in nodes:
            graph.add_node(node)
            graph.add_edge(ParallelEdge(source=start.id, target=node.id))
            graph.add_edge(Edge(source=node.id, target=end.id))

        return graph