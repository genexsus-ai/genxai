"""
Graph Visualization Demo

This example demonstrates the new visualization capabilities of GenXAI graphs:
- draw_ascii(): ASCII art representation
- to_mermaid(): Mermaid diagram syntax
- to_dot(): GraphViz DOT format
- print_structure(): Simple text summary
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import (
    InputNode,
    OutputNode,
    AgentNode,
    ConditionNode,
    ToolNode,
)
from genxai.core.graph.edges import Edge, ConditionalEdge, ParallelEdge


def create_sequential_graph() -> Graph:
    """Create a simple sequential workflow graph."""
    graph = Graph(name="sequential_workflow")

    # Add nodes
    graph.add_node(InputNode("input"))
    graph.add_node(AgentNode("collector", "data_collector"))
    graph.add_node(AgentNode("processor", "data_processor"))
    graph.add_node(AgentNode("analyzer", "data_analyzer"))
    graph.add_node(OutputNode("output"))

    # Add edges
    graph.add_edge(Edge(source="input", target="collector"))
    graph.add_edge(Edge(source="collector", target="processor"))
    graph.add_edge(Edge(source="processor", target="analyzer"))
    graph.add_edge(Edge(source="analyzer", target="output"))

    return graph


def create_conditional_graph() -> Graph:
    """Create a graph with conditional branching."""
    graph = Graph(name="conditional_workflow")

    # Add nodes
    graph.add_node(InputNode("input"))
    graph.add_node(ConditionNode("classifier", "classify_request"))
    graph.add_node(AgentNode("technical_support", "tech_agent"))
    graph.add_node(AgentNode("billing_support", "billing_agent"))
    graph.add_node(AgentNode("general_support", "general_agent"))
    graph.add_node(OutputNode("output"))

    # Add edges
    graph.add_edge(Edge(source="input", target="classifier"))

    # Conditional edges from classifier
    graph.add_edge(
        ConditionalEdge(
            source="classifier",
            target="technical_support",
            condition=lambda state: state.get("category") == "technical",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="classifier",
            target="billing_support",
            condition=lambda state: state.get("category") == "billing",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="classifier",
            target="general_support",
            condition=lambda state: state.get("category") == "general",
        )
    )

    # All paths lead to output
    graph.add_edge(Edge(source="technical_support", target="output"))
    graph.add_edge(Edge(source="billing_support", target="output"))
    graph.add_edge(Edge(source="general_support", target="output"))

    return graph


def create_parallel_graph() -> Graph:
    """Create a graph with parallel execution."""
    graph = Graph(name="parallel_workflow")

    # Add nodes
    graph.add_node(InputNode("input"))
    graph.add_node(AgentNode("coordinator", "coordinator_agent"))
    graph.add_node(AgentNode("technical_analyst", "tech_analyst"))
    graph.add_node(AgentNode("business_analyst", "biz_analyst"))
    graph.add_node(AgentNode("risk_analyst", "risk_analyst"))
    graph.add_node(AgentNode("aggregator", "aggregator_agent"))
    graph.add_node(OutputNode("output"))

    # Add edges
    graph.add_edge(Edge(source="input", target="coordinator"))

    # Parallel edges from coordinator to analysts
    graph.add_edge(ParallelEdge(source="coordinator", target="technical_analyst"))
    graph.add_edge(ParallelEdge(source="coordinator", target="business_analyst"))
    graph.add_edge(ParallelEdge(source="coordinator", target="risk_analyst"))

    # All analysts feed into aggregator
    graph.add_edge(Edge(source="technical_analyst", target="aggregator"))
    graph.add_edge(Edge(source="business_analyst", target="aggregator"))
    graph.add_edge(Edge(source="risk_analyst", target="aggregator"))

    # Aggregator to output
    graph.add_edge(Edge(source="aggregator", target="output"))

    return graph


def create_complex_graph() -> Graph:
    """Create a complex graph with multiple patterns."""
    graph = Graph(name="complex_workflow")

    # Add nodes
    graph.add_node(InputNode("input"))
    graph.add_node(AgentNode("validator", "validator_agent"))
    graph.add_node(ConditionNode("router", "route_decision"))
    graph.add_node(AgentNode("fast_path", "fast_processor"))
    graph.add_node(AgentNode("slow_path_1", "detailed_analyzer"))
    graph.add_node(AgentNode("slow_path_2", "quality_checker"))
    graph.add_node(ToolNode("enrichment", "data_enrichment_tool"))
    graph.add_node(AgentNode("final_processor", "final_agent"))
    graph.add_node(OutputNode("output"))

    # Add edges
    graph.add_edge(Edge(source="input", target="validator"))
    graph.add_edge(Edge(source="validator", target="router"))

    # Conditional routing
    graph.add_edge(
        ConditionalEdge(
            source="router",
            target="fast_path",
            condition=lambda state: state.get("priority") == "high",
        )
    )
    graph.add_edge(
        ConditionalEdge(
            source="router",
            target="slow_path_1",
            condition=lambda state: state.get("priority") == "low",
        )
    )

    # Sequential slow path
    graph.add_edge(Edge(source="slow_path_1", target="slow_path_2"))

    # Parallel enrichment
    graph.add_edge(ParallelEdge(source="fast_path", target="enrichment"))
    graph.add_edge(ParallelEdge(source="slow_path_2", target="enrichment"))

    # Convergence
    graph.add_edge(Edge(source="fast_path", target="final_processor"))
    graph.add_edge(Edge(source="slow_path_2", target="final_processor"))
    graph.add_edge(Edge(source="enrichment", target="final_processor"))
    graph.add_edge(Edge(source="final_processor", target="output"))

    return graph


def demo_visualization(graph: Graph, title: str) -> None:
    """Demonstrate all visualization methods for a graph."""
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80)

    # 1. Print structure (simple summary)
    print("\n1. PRINT STRUCTURE (Simple Summary)")
    print("-" * 80)
    graph.print_structure()

    # 2. ASCII art visualization
    print("\n2. ASCII ART VISUALIZATION")
    print("-" * 80)
    print(graph.draw_ascii())

    # 3. Mermaid diagram syntax
    print("\n3. MERMAID DIAGRAM SYNTAX")
    print("-" * 80)
    print("(Copy this to https://mermaid.live/ to visualize)")
    print()
    print("```mermaid")
    print(graph.to_mermaid())
    print("```")

    # 4. GraphViz DOT format
    print("\n4. GRAPHVIZ DOT FORMAT")
    print("-" * 80)
    print("(Save to .dot file and render with: dot -Tpng graph.dot -o graph.png)")
    print()
    print(graph.to_dot())

    print("\n" + "=" * 80)
    print()


def main() -> None:
    """Run all visualization demos."""
    print("\n" + "=" * 80)
    print("GENXAI GRAPH VISUALIZATION DEMO")
    print("=" * 80)
    print()
    print("This demo showcases the new visualization capabilities:")
    print("  • draw_ascii()     - ASCII art for console output")
    print("  • to_mermaid()     - Mermaid syntax for documentation")
    print("  • to_dot()         - GraphViz DOT for professional diagrams")
    print("  • print_structure() - Quick text summary")
    print()

    # Demo 1: Sequential workflow
    sequential_graph = create_sequential_graph()
    demo_visualization(sequential_graph, "DEMO 1: Sequential Workflow")

    # Demo 2: Conditional branching
    conditional_graph = create_conditional_graph()
    demo_visualization(conditional_graph, "DEMO 2: Conditional Branching")

    # Demo 3: Parallel execution
    parallel_graph = create_parallel_graph()
    demo_visualization(parallel_graph, "DEMO 3: Parallel Execution")

    # Demo 4: Complex workflow
    complex_graph = create_complex_graph()
    demo_visualization(complex_graph, "DEMO 4: Complex Multi-Pattern Workflow")

    # Summary
    print("\n" + "=" * 80)
    print("VISUALIZATION DEMO COMPLETE!")
    print("=" * 80)
    print()
    print("Key Features:")
    print("  ✓ Multiple visualization formats for different use cases")
    print("  ✓ Handles sequential, conditional, and parallel patterns")
    print("  ✓ Shows node types and statuses")
    print("  ✓ Detects and handles cycles")
    print("  ✓ No external dependencies required")
    print()
    print("Usage Tips:")
    print("  • Use draw_ascii() for quick console debugging")
    print("  • Use to_mermaid() for documentation and README files")
    print("  • Use to_dot() for professional presentations")
    print("  • Use print_structure() for quick overview")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
