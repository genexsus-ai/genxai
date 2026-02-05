"""
Sequential Pattern - Linear Agent Chain

This pattern demonstrates a simple linear workflow where agents execute
one after another in sequence. Each agent's output becomes the next agent's input.

Use Cases:
- Document processing pipelines
- Data transformation chains
- Step-by-step analysis workflows
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import Agent, AgentFactory


async def main():
    """Run sequential pattern example."""
    print("=" * 70)
    print("SEQUENTIAL PATTERN - Linear Agent Chain")
    print("=" * 70)
    print()

    # Create agents for sequential processing
    print("Creating agents...")
    
    # Agent 1: Data Collector
    collector = AgentFactory.create_agent(
        id="collector",
        role="Data Collector",
        goal="Gather raw data from input",
        backstory="Expert at extracting and organizing raw information",
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    # Agent 2: Data Processor
    processor = AgentFactory.create_agent(
        id="processor",
        role="Data Processor",
        goal="Clean and transform collected data",
        backstory="Specialist in data cleaning and transformation",
        tools=["calculator", "data_validator"],
        llm_model="gpt-4",
        temperature=0.2,
    )
    
    # Agent 3: Data Analyzer
    analyzer = AgentFactory.create_agent(
        id="analyzer",
        role="Data Analyzer",
        goal="Analyze processed data and extract insights",
        backstory="Expert at finding patterns and generating insights",
        llm_model="gpt-4",
        temperature=0.5,
    )
    
    # Agent 4: Report Generator
    reporter = AgentFactory.create_agent(
        id="reporter",
        role="Report Generator",
        goal="Create comprehensive report from analysis",
        backstory="Professional report writer with clear communication skills",
        llm_model="gpt-4",
        temperature=0.7,
    )
    
    print(f"✓ Created {4} agents")
    print()

    # Build sequential graph
    print("Building sequential workflow graph...")
    graph = Graph(name="sequential_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="collector_node", agent_id="collector"))
    graph.add_node(AgentNode(id="processor_node", agent_id="processor"))
    graph.add_node(AgentNode(id="analyzer_node", agent_id="analyzer"))
    graph.add_node(AgentNode(id="reporter_node", agent_id="reporter"))
    graph.add_node(OutputNode())
    
    # Add sequential edges (linear chain)
    graph.add_edge(Edge(source="input", target="collector_node"))
    graph.add_edge(Edge(source="collector_node", target="processor_node"))
    graph.add_edge(Edge(source="processor_node", target="analyzer_node"))
    graph.add_edge(Edge(source="analyzer_node", target="reporter_node"))
    graph.add_edge(Edge(source="reporter_node", target="output"))
    
    print(f"✓ Graph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print()

    # Validate graph
    print("Validating graph structure...")
    try:
        graph.validate()
        print("✓ Graph validation passed")
    except Exception as e:
        print(f"✗ Graph validation failed: {e}")
        return
    print()

    # Visualize workflow
    print("Workflow Structure:")
    print("-" * 70)
    print("Input → Collector → Processor → Analyzer → Reporter → Output")
    print("-" * 70)
    print()

    # Execute workflow
    print("Executing sequential workflow...")
    print("-" * 70)
    
    input_data = {
        "task": "Analyze sales data for Q4 2025",
        "data": {
            "sales": [1000, 1500, 2000, 2500, 3000],
            "regions": ["North", "South", "East", "West", "Central"],
            "products": ["Product A", "Product B", "Product C"]
        }
    }
    
    print(f"Input: {input_data['task']}")
    print()
    
    # Simulate execution (in real scenario with API key)
    print("Execution Flow:")
    print("  1. Collector: Gathering sales data...")
    print("     → Collected 5 data points across 5 regions")
    print()
    print("  2. Processor: Cleaning and transforming data...")
    print("     → Normalized values, removed outliers")
    print()
    print("  3. Analyzer: Analyzing processed data...")
    print("     → Identified growth trend: +25% QoQ")
    print("     → Best performing region: Central (+50%)")
    print()
    print("  4. Reporter: Generating final report...")
    print("     → Created comprehensive Q4 analysis report")
    print()
    
    # In real scenario with API key:
    # result = await graph.run(input_data=input_data)
    
    print("-" * 70)
    print("✓ Sequential workflow completed successfully")
    print()

    # Display results
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print("Final Report:")
    print("-" * 70)
    print("Q4 2025 Sales Analysis")
    print()
    print("Key Findings:")
    print("  • Total sales increased by 25% compared to Q3")
    print("  • Central region showed exceptional growth (+50%)")
    print("  • Product A remains top performer")
    print("  • Recommendation: Expand operations in Central region")
    print("-" * 70)
    print()

    # Pattern characteristics
    print("=" * 70)
    print("SEQUENTIAL PATTERN CHARACTERISTICS")
    print("=" * 70)
    print()
    print("Advantages:")
    print("  ✓ Simple and easy to understand")
    print("  ✓ Predictable execution flow")
    print("  ✓ Easy to debug and trace")
    print("  ✓ Clear data lineage")
    print()
    print("Disadvantages:")
    print("  ✗ No parallelization (slower for independent tasks)")
    print("  ✗ Single point of failure (one agent fails = workflow fails)")
    print("  ✗ Cannot handle conditional logic")
    print()
    print("Best Used For:")
    print("  • Document processing pipelines")
    print("  • ETL (Extract-Transform-Load) workflows")
    print("  • Step-by-step analysis")
    print("  • Linear data transformations")
    print()


if __name__ == "__main__":
    asyncio.run(main())
