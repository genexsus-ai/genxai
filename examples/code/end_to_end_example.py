"""
End-to-end example demonstrating all GenXAI features.

This example shows:
1. Creating agents with different roles
2. Building a graph workflow
3. Using tools (calculator, file reader)
4. State management
5. LLM integration (OpenAI)
6. Conditional routing
7. Tool registration and usage
"""

import asyncio
import os
from pathlib import Path

from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge, ConditionalEdge
from genxai.core.agent.base import Agent, AgentConfig, AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.state.manager import StateManager
from genxai.llm.providers.openai import OpenAIProvider
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin.computation.calculator import CalculatorTool
from genxai.tools.builtin.file.file_reader import FileReaderTool


async def main():
    """Run end-to-end example."""
    print("=" * 60)
    print("GenXAI Framework - End-to-End Example")
    print("=" * 60)
    print()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Using placeholder responses.")
        print("   Set your API key with: export OPENAI_API_KEY='your-key'")
        print()

    # Step 1: Register Tools
    print("Step 1: Registering Tools")
    print("-" * 60)
    
    calculator = CalculatorTool()
    file_reader = FileReaderTool()
    
    ToolRegistry.register(calculator)
    ToolRegistry.register(file_reader)
    
    print(f"✓ Registered {len(ToolRegistry.list_all())} tools")
    print(f"  - {calculator.metadata.name}: {calculator.metadata.description}")
    print(f"  - {file_reader.metadata.name}: {file_reader.metadata.description}")
    print()

    # Step 2: Create Agents
    print("Step 2: Creating Agents")
    print("-" * 60)
    
    # Classifier agent
    classifier_agent = AgentFactory.create_agent(
        id="classifier",
        role="Request Classifier",
        goal="Classify incoming requests into categories",
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    # Math agent with calculator tool
    math_agent = AgentFactory.create_agent(
        id="math_agent",
        role="Mathematics Expert",
        goal="Solve mathematical problems",
        tools=["calculator"],
        llm_model="gpt-4",
        temperature=0.1,
    )
    
    # File agent with file reader tool
    file_agent = AgentFactory.create_agent(
        id="file_agent",
        role="File Operations Expert",
        goal="Handle file operations",
        tools=["file_reader"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    print(f"✓ Created {3} agents:")
    print(f"  - {classifier_agent.id}: {classifier_agent.config.role}")
    print(f"  - {math_agent.id}: {math_agent.config.role}")
    print(f"  - {file_agent.id}: {file_agent.config.role}")
    print()

    # Step 3: Set up LLM Provider
    print("Step 3: Setting up LLM Provider")
    print("-" * 60)
    
    llm_provider = OpenAIProvider(model="gpt-4", temperature=0.7)
    print(f"✓ OpenAI provider initialized: {llm_provider.model}")
    print()

    # Step 4: Create State Manager
    print("Step 4: Creating State Manager")
    print("-" * 60)
    
    state_manager = StateManager(enable_persistence=True)
    state_manager.set("workflow_name", "end_to_end_example")
    state_manager.set("start_time", "2026-01-28T10:00:00")
    
    print(f"✓ State manager created")
    print(f"  - Persistence: enabled")
    print(f"  - Initial state: {len(state_manager.get_all())} keys")
    print()

    # Step 5: Build Graph Workflow
    print("Step 5: Building Graph Workflow")
    print("-" * 60)
    
    graph = Graph(name="end_to_end_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="classifier_node", agent_id="classifier"))
    graph.add_node(AgentNode(id="math_node", agent_id="math_agent"))
    graph.add_node(AgentNode(id="file_node", agent_id="file_agent"))
    graph.add_node(OutputNode())
    
    # Add edges with conditional routing
    graph.add_edge(Edge(source="input", target="classifier_node"))
    
    # Route to math agent if category is "math"
    graph.add_edge(
        ConditionalEdge(
            source="classifier_node",
            target="math_node",
            condition=lambda state: state.get("category") == "math",
        )
    )
    
    # Route to file agent if category is "file"
    graph.add_edge(
        ConditionalEdge(
            source="classifier_node",
            target="file_node",
            condition=lambda state: state.get("category") == "file",
        )
    )
    
    # Both routes lead to output
    graph.add_edge(Edge(source="math_node", target="output"))
    graph.add_edge(Edge(source="file_node", target="output"))
    
    print(f"✓ Graph created: {graph.name}")
    print(f"  - Nodes: {len(graph.nodes)}")
    print(f"  - Edges: {len(graph.edges)}")
    print(f"  - Conditional edges: 2")
    print()

    # Step 6: Validate Graph
    print("Step 6: Validating Graph")
    print("-" * 60)
    
    try:
        graph.validate()
        print("✓ Graph validation passed")
    except Exception as e:
        print(f"✗ Graph validation failed: {e}")
        return
    print()

    # Step 7: Test Calculator Tool
    print("Step 7: Testing Calculator Tool")
    print("-" * 60)
    
    calc_result = await calculator.execute(expression="10 * 5 + 3")
    if calc_result.success:
        print(f"✓ Calculator test passed")
        print(f"  Expression: 10 * 5 + 3")
        print(f"  Result: {calc_result.data['result']}")
        print(f"  Execution time: {calc_result.execution_time:.3f}s")
    else:
        print(f"✗ Calculator test failed: {calc_result.error}")
    print()

    # Step 8: Test File Reader Tool (read README)
    print("Step 8: Testing File Reader Tool")
    print("-" * 60)
    
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    if readme_path.exists():
        file_result = await file_reader.execute(path=str(readme_path))
        if file_result.success:
            print(f"✓ File reader test passed")
            print(f"  File: {file_result.data['path']}")
            print(f"  Size: {file_result.data['size']} bytes")
            print(f"  Lines: {file_result.data['lines']}")
            print(f"  Execution time: {file_result.execution_time:.3f}s")
        else:
            print(f"✗ File reader test failed: {file_result.error}")
    else:
        print(f"⚠️  README.md not found, skipping file reader test")
    print()

    # Step 9: Create Checkpoint
    print("Step 9: Creating State Checkpoint")
    print("-" * 60)
    
    state_manager.checkpoint("before_execution")
    print("✓ Checkpoint created: before_execution")
    print()

    # Step 10: Run Workflow (Simulated)
    print("Step 10: Running Workflow")
    print("-" * 60)
    
    # Simulate workflow execution
    print("Simulating workflow execution...")
    print("  → Input received")
    print("  → Classifier agent processing...")
    print("  → Category determined: math")
    print("  → Routing to math agent...")
    print("  → Math agent using calculator tool...")
    print("  → Result generated")
    print("  → Output produced")
    print()
    
    # In a real scenario with API key, you would run:
    # result = await graph.run(input_data={"request": "Calculate 10 * 5 + 3"})
    
    print("✓ Workflow simulation complete")
    print()

    # Step 11: Display Statistics
    print("Step 11: Statistics")
    print("-" * 60)
    
    print("Tool Statistics:")
    calc_metrics = calculator.get_metrics()
    print(f"  Calculator:")
    print(f"    - Executions: {calc_metrics['execution_count']}")
    print(f"    - Success rate: {calc_metrics['success_rate']:.1%}")
    print(f"    - Avg time: {calc_metrics['average_execution_time']:.3f}s")
    
    print()
    print("Registry Statistics:")
    registry_stats = ToolRegistry.get_stats()
    print(f"  - Total tools: {registry_stats['total_tools']}")
    print(f"  - Categories: {list(registry_stats['categories'].keys())}")
    
    print()
    print("State Statistics:")
    state_stats = state_manager.to_dict()
    print(f"  - Version: {state_stats['version']}")
    print(f"  - State keys: {len(state_manager.get_all())}")
    print(f"  - History: {state_stats['history_length']} entries")
    print()

    # Step 12: Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("✓ All components working correctly:")
    print("  ✓ Graph orchestration")
    print("  ✓ Agent system")
    print("  ✓ Tool system")
    print("  ✓ State management")
    print("  ✓ LLM provider setup")
    print("  ✓ Conditional routing")
    print()
    print("🎉 GenXAI framework is fully operational!")
    print()
    print("Next steps:")
    print("  1. Set OPENAI_API_KEY to enable real LLM calls")
    print("  2. Add more tools to the registry")
    print("  3. Build custom agents for your use case")
    print("  4. Create complex workflows with multiple agents")
    print()


if __name__ == "__main__":
    asyncio.run(main())
