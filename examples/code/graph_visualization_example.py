"""Generate ASCII, Mermaid, and DOT outputs for a workflow graph."""

from genxai.core.graph import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge


def main() -> None:
    graph = Graph(name="visual_demo")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="research_node", agent_id="researcher"))
    graph.add_node(AgentNode(id="writer_node", agent_id="writer"))
    graph.add_node(OutputNode())

    graph.add_edge(Edge(source="input", target="research_node"))
    graph.add_edge(Edge(source="research_node", target="writer_node"))
    graph.add_edge(Edge(source="writer_node", target="output"))

    print(graph.draw_ascii())
    print("\nMermaid:\n", graph.to_mermaid())
    print("\nDOT:\n", graph.to_dot())


if __name__ == "__main__":
    main()