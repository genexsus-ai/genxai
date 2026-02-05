"""Round-robin flow orchestrator."""

from typing import List

from genxai.core.graph.engine import Graph
from genxai.core.graph.edges import Edge
from genxai.core.graph.nodes import AgentNode
from genxai.flows.base import FlowOrchestrator


class RoundRobinFlow(FlowOrchestrator):
    """Execute agents in a fixed, round-robin sequence."""

    def build_graph(self) -> Graph:
        graph = Graph(name=self.name)
        nodes: List[AgentNode] = self._agent_nodes()

        for node in nodes:
            graph.add_node(node)

        for idx in range(len(nodes) - 1):
            graph.add_edge(Edge(source=nodes[idx].id, target=nodes[idx + 1].id))

        return graph