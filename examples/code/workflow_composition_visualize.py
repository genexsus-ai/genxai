"""Generate diagrams for the global workflow composition example."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from genxai import AgentFactory
from genxai.core.graph.engine import Graph
from genxai.core.graph.edges import ConditionalEdge, Edge, ParallelEdge
from genxai.core.graph.nodes import (
    AgentNode,
    ConditionNode,
    InputNode,
    LoopNode,
    OutputNode,
    SubgraphNode,
    ToolNode,
)


def build_global_graph() -> Graph:
    """Build the global workflow graph with deterministic routing + subflows."""
    graph = Graph(name="global_orchestrator")

    graph.add_node(InputNode(id="input"))
    graph.add_node(ConditionNode(id="route", condition="route_rule"))
    graph.add_node(SubgraphNode(id="support_subflow", workflow_id="support_subflow"))
    graph.add_node(SubgraphNode(id="sales_subflow", workflow_id="sales_subflow"))
    graph.add_node(SubgraphNode(id="fallback_subflow", workflow_id="fallback_subflow"))

    router_agent = AgentFactory.create_agent(
        id="router_agent",
        role="Router",
        goal="Finalize routing decision",
        temperature=0.0,
        seed=42,
    )
    graph.add_node(ToolNode(id="read_file", tool_name="file_reader"))
    graph.add_node(ToolNode(id="fetch_url", tool_name="api_caller"))
    graph.add_node(ToolNode(id="validate_url", tool_name="url_validator"))
    graph.add_node(ToolNode(id="write_file", tool_name="file_writer"))
    graph.add_node(ToolNode(id="query_db", tool_name="sql_query"))
    graph.add_node(LoopNode(id="retry_checks", condition="retry_needed", max_iterations=2))
    graph.add_node(ToolNode(id="send_email", tool_name="email_sender"))
    graph.add_node(ToolNode(id="notify_slack", tool_name="slack_notifier"))
    graph.add_node(ToolNode(id="call_webhook", tool_name="webhook_caller"))
    graph.add_node(AgentNode(id="router_agent", agent_id=router_agent.id))
    graph.add_node(ConditionNode(id="post_route", condition="post_action"))
    graph.add_node(ToolNode(id="archive_report", tool_name="file_writer"))
    graph.add_node(ToolNode(id="escalate_ticket", tool_name="email_sender"))
    graph.add_node(OutputNode(id="output"))

    graph.add_edge(Edge(source="input", target="route"))
    graph.add_edge(
        ConditionalEdge(
            source="route",
            target="support_subflow",
            condition=lambda state: state.get("route") == "support",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="route",
            target="sales_subflow",
            condition=lambda state: state.get("route") == "sales",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="route",
            target="fallback_subflow",
            condition=lambda state: state.get("route") not in {"support", "sales"},
        )
    )
    graph.add_edge(Edge(source="support_subflow", target="read_file"))
    graph.add_edge(Edge(source="sales_subflow", target="read_file"))
    graph.add_edge(Edge(source="fallback_subflow", target="read_file"))
    graph.add_edge(Edge(source="read_file", target="fetch_url"))
    graph.add_edge(Edge(source="fetch_url", target="validate_url"))
    graph.add_edge(Edge(source="validate_url", target="write_file"))
    graph.add_edge(Edge(source="write_file", target="query_db"))
    graph.add_edge(Edge(source="query_db", target="retry_checks"))
    graph.add_edge(ConditionalEdge(
        source="retry_checks",
        target="query_db",
        condition=lambda state: state.get("retry_needed") is True,
    ))
    graph.add_edge(Edge(source="retry_checks", target="send_email"))
    graph.add_edge(ParallelEdge(source="send_email", target="notify_slack"))
    graph.add_edge(ParallelEdge(source="send_email", target="call_webhook"))
    graph.add_edge(Edge(source="notify_slack", target="router_agent"))
    graph.add_edge(Edge(source="call_webhook", target="router_agent"))
    graph.add_edge(Edge(source="router_agent", target="post_route"))
    graph.add_edge(
        ConditionalEdge(
            source="post_route",
            target="archive_report",
            condition=lambda state: state.get("post_action") == "archive",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="post_route",
            target="escalate_ticket",
            condition=lambda state: state.get("post_action") == "escalate",
        )
    )
    graph.add_edge(Edge(source="archive_report", target="output"))
    graph.add_edge(Edge(source="escalate_ticket", target="output"))

    return graph


def main() -> None:
    graph = build_global_graph()

    print("ASCII preview:\n")
    print(graph.draw_ascii())

    diagrams_dir = Path("docs/diagrams")
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    mermaid_path = diagrams_dir / "workflow_composition.mmd"
    dot_path = diagrams_dir / "workflow_composition.dot"
    svg_path = diagrams_dir / "workflow_composition.svg"
    png_path = diagrams_dir / "workflow_composition.png"
    json_path = diagrams_dir / "workflow_composition.json"

    mermaid_output = graph.to_mermaid().replace("graph TD", "graph LR", 1)
    dot_output = graph.to_dot().replace("rankdir=TB", "rankdir=LR", 1)
    mermaid_path.write_text(mermaid_output)
    dot_path.write_text(dot_output)

    graph_json = {
        "name": graph.name,
        "nodes": [
            {"id": node.id, "type": node.type.value, "config": node.config.data}
            for node in graph.nodes.values()
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "condition": (
                    getattr(edge, "condition", None).__name__
                    if callable(getattr(edge, "condition", None))
                    else getattr(edge, "condition", None)
                ),
                "parallel": edge.metadata.get("parallel", False),
            }
            for edge in graph.edges
        ],
    }
    json_path.write_text(json.dumps(graph_json, indent=2))

    print(f"Mermaid diagram saved to {mermaid_path}")
    print(f"DOT diagram saved to {dot_path}")
    print(f"JSON snapshot saved to {json_path}")

    try:
        subprocess.run(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)], check=True)
        subprocess.run(["dot", "-Tpng", str(dot_path), "-o", str(png_path)], check=True)
        print(f"SVG diagram rendered to {svg_path}")
        print(f"PNG diagram rendered to {png_path}")
    except FileNotFoundError:
        print("GraphViz not installed. Skipping SVG/PNG render.")
    except subprocess.CalledProcessError as exc:
        print(f"GraphViz render failed: {exc}")


if __name__ == "__main__":
    main()