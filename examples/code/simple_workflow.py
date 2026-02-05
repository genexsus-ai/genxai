"""Simple workflow example demonstrating basic graph execution."""

import asyncio
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge, ConditionalEdge


async def main() -> None:
    """Run a simple workflow example."""
    # Create a new graph
    graph = Graph(name="simple_workflow")

    # Register agent used by the workflow
    processing_agent = AgentFactory.create_agent(
        id="processing_agent",
        role="Processor",
        goal="Process input and return a response",
    )
    AgentRegistry.register(processing_agent)

    # Add nodes
    input_node = InputNode()
    agent_node = AgentNode(id="processor", agent_id="processing_agent")
    output_node = OutputNode()

    graph.add_node(input_node)
    graph.add_node(agent_node)
    graph.add_node(output_node)

    # Add edges
    graph.add_edge(Edge(source="input", target="processor"))
    graph.add_edge(Edge(source="processor", target="output"))

    # Run the workflow
    print("Running simple workflow...")
    result = await graph.run(input_data={"message": "Hello, GenXAI!"})

    print(f"\nWorkflow completed!")
    print(f"Result: {result}")


async def conditional_workflow() -> None:
    """Run a workflow with conditional edges."""
    # Create graph
    graph = Graph(name="conditional_workflow")

    # Register agents used by the workflow
    classifier_agent = AgentFactory.create_agent(
        id="classifier_agent",
        role="Classifier",
        goal="Classify input into categories",
    )
    agent_a = AgentFactory.create_agent(
        id="agent_a",
        role="Agent A",
        goal="Handle category A",
    )
    agent_b = AgentFactory.create_agent(
        id="agent_b",
        role="Agent B",
        goal="Handle category B",
    )
    AgentRegistry.register(classifier_agent)
    AgentRegistry.register(agent_a)
    AgentRegistry.register(agent_b)

    # Add nodes
    input_node = InputNode()
    classifier = AgentNode(id="classifier", agent_id="classifier_agent")
    path_a = AgentNode(id="path_a", agent_id="agent_a")
    path_b = AgentNode(id="path_b", agent_id="agent_b")
    output_node = OutputNode()

    graph.add_node(input_node)
    graph.add_node(classifier)
    graph.add_node(path_a)
    graph.add_node(path_b)
    graph.add_node(output_node)

    # Add edges with conditions
    graph.add_edge(Edge(source="input", target="classifier"))

    # Conditional routing based on classification
    graph.add_edge(
        ConditionalEdge(
            source="classifier",
            target="path_a",
            condition=lambda state: state.get("classifier", {}).get("category") == "A",
        )
    )

    graph.add_edge(
        ConditionalEdge(
            source="classifier",
            target="path_b",
            condition=lambda state: state.get("classifier", {}).get("category") == "B",
        )
    )

    graph.add_edge(Edge(source="path_a", target="output"))
    graph.add_edge(Edge(source="path_b", target="output"))

    # Run workflow
    print("\nRunning conditional workflow...")
    result = await graph.run(input_data={"text": "Sample input for classification"})

    print(f"\nConditional workflow completed!")
    print(f"Result: {result}")


if __name__ == "__main__":
    # Run simple workflow
    asyncio.run(main())

    # Run conditional workflow
    asyncio.run(conditional_workflow())
