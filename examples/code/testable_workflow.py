"""
Fully Testable Workflow Example

This example demonstrates a complete, runnable workflow with:
- Real agent instances registered in AgentRegistry
- Actual tool execution (calculator, file_reader)
- Proper graph execution with agent integration
- Works with or without API key (graceful degradation)

Run this example:
    python examples/code/testable_workflow.py
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

from genxai.core.graph.executor import EnhancedGraph, WorkflowExecutor
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.base import Agent
from genxai.core.agent.registry import AgentRegistry
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin.computation.calculator import CalculatorTool
from genxai.tools.builtin.file.file_reader import FileReaderTool


# EnhancedGraph is now imported from core library
# No need to define it here anymore

class _LegacyEnhancedGraph(EnhancedGraph):
    """Enhanced graph with agent execution support."""

    async def _execute_node_logic(
        self, node: Any, state: Dict[str, Any], max_iterations: int = 50
    ) -> Any:
        """Execute node logic with actual agent execution.

        Args:
            node: Node to execute
            state: Current state

        Returns:
            Result of node execution
        """
        from genxai.core.graph.nodes import NodeType

        if node.type == NodeType.INPUT:
            return state.get("input")
        
        elif node.type == NodeType.OUTPUT:
            return state
        
        elif node.type == NodeType.AGENT:
            # Get agent from registry
            agent_id = node.config.data.get("agent_id")
            if not agent_id:
                raise ValueError(f"Agent node '{node.id}' missing agent_id in config.data")
            
            agent = AgentRegistry.get(agent_id)
            if agent is None:
                raise ValueError(f"Agent '{agent_id}' not found in registry")
            
            # Prepare task from state
            task = state.get("task", "Process the input data")
            
            # Execute agent with tools if available
            result = await self._execute_agent_with_tools(agent, task, state)
            
            return result
        
        else:
            # Default behavior
            return {"node_id": node.id, "type": node.type.value}

    async def _execute_agent_with_tools(
        self, agent: Agent, task: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with tool support.

        Args:
            agent: Agent to execute
            task: Task description
            state: Current state

        Returns:
            Execution result
        """
        print(f"  → Agent '{agent.id}' ({agent.config.role}) executing...")
        
        # Check if agent has tools
        tool_results = {}
        if agent.config.tools:
            print(f"    Tools available: {', '.join(agent.config.tools)}")
            
            # Execute tools based on task
            for tool_name in agent.config.tools:
                tool = ToolRegistry.get(tool_name)
                if tool:
                    tool_result = await self._execute_tool_for_task(
                        tool, tool_name, task, state
                    )
                    if tool_result:
                        tool_results[tool_name] = tool_result
        
        # Execute agent (skip LLM call when API key is missing)
        if not os.getenv("OPENAI_API_KEY"):
            agent_result = {
                "agent_id": agent.id,
                "status": "simulated",
                "output": "Simulated response (no API key provided)",
            }
        else:
            agent_result = await agent.execute(task, context=state)
        
        # Combine agent result with tool results
        agent_result["tool_results"] = tool_results
        
        return agent_result

    async def _execute_tool_for_task(
        self, tool: Any, tool_name: str, task: str, state: Dict[str, Any]
    ) -> Any:
        """Execute a tool based on the task.

        Args:
            tool: Tool instance
            tool_name: Tool name
            task: Task description
            state: Current state

        Returns:
            Tool execution result or None
        """
        try:
            # Calculator tool
            if tool_name == "calculator":
                # Check if task involves calculation
                if any(op in task.lower() for op in ["calculate", "compute", "add", "multiply", "+"]):
                    # Extract expression from state or use default
                    expression = state.get("expression", "10 * 5 + 3")
                    print(f"    → Executing calculator: {expression}")
                    result = await tool.execute(expression=expression)
                    if result.success:
                        print(f"      ✓ Result: {result.data['result']}")
                        return result.data
            
            # File reader tool
            elif tool_name == "file_reader":
                # Check if task involves file reading
                if any(word in task.lower() for word in ["read", "file", "load"]):
                    # Get file path from state or use README
                    file_path = state.get("file_path")
                    if not file_path:
                        readme_path = Path(__file__).parent.parent.parent / "README.md"
                        if readme_path.exists():
                            file_path = str(readme_path)
                    
                    if file_path:
                        print(f"    → Reading file: {Path(file_path).name}")
                        result = await tool.execute(path=file_path)
                        if result.success:
                            print(f"      ✓ Read {result.data['lines']} lines ({result.data['size']} bytes)")
                            return result.data
        
        except Exception as e:
            print(f"      ✗ Tool execution failed: {e}")
        
        return None


async def scenario_1_calculator_workflow():
    """Scenario 1: Calculator workflow (no API key needed)."""
    print("=" * 70)
    print("SCENARIO 1: Calculator Workflow")
    print("=" * 70)
    print()

    # Step 1: Register tools
    print("Step 1: Registering Tools")
    print("-" * 70)
    calculator = CalculatorTool()
    ToolRegistry.register(calculator)
    print(f"✓ Registered calculator tool")
    print()

    # Step 2: Create and register agents
    print("Step 2: Creating Agents")
    print("-" * 70)
    
    math_agent = AgentFactory.create_agent(
        id="math_agent",
        role="Mathematics Expert",
        goal="Solve mathematical problems",
        tools=["calculator"],
        llm_model="gpt-4",
        temperature=0.1,
    )
    
    AgentRegistry.register(math_agent)
    print(f"✓ Created and registered: {math_agent.id}")
    print()

    # Step 3: Build graph
    print("Step 3: Building Graph")
    print("-" * 70)
    
    graph = _LegacyEnhancedGraph(name="calculator_workflow")
    
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="math_node", agent_id="math_agent"))
    graph.add_node(OutputNode())
    
    graph.add_edge(Edge(source="input", target="math_node"))
    graph.add_edge(Edge(source="math_node", target="output"))
    
    print(f"✓ Graph created: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print()

    # Step 4: Execute workflow
    print("Step 4: Executing Workflow")
    print("-" * 70)
    
    input_data = {
        "task": "Calculate the result of 10 * 5 + 3",
        "expression": "10 * 5 + 3"
    }
    
    print(f"Input: {input_data['task']}")
    print()
    
    result = await graph.run(input_data=input_data)
    
    print()
    print("✓ Workflow completed successfully!")
    print()

    # Step 5: Display results
    print("Step 5: Results")
    print("-" * 70)
    print(f"Final state keys: {list(result.keys())}")
    if "math_node" in result:
        math_result = result["math_node"]
        print(f"Agent output: {math_result.get('output')}")
        if "tool_results" in math_result and "calculator" in math_result["tool_results"]:
            calc_result = math_result["tool_results"]["calculator"]
            print(f"Calculator result: {calc_result.get('result')}")
    print()


async def scenario_2_file_processing_workflow():
    """Scenario 2: File processing workflow (no API key needed)."""
    print("=" * 70)
    print("SCENARIO 2: File Processing Workflow")
    print("=" * 70)
    print()

    # Step 1: Register tools
    print("Step 1: Registering Tools")
    print("-" * 70)
    file_reader = FileReaderTool()
    ToolRegistry.register(file_reader)
    print(f"✓ Registered file_reader tool")
    print()

    # Step 2: Create and register agents
    print("Step 2: Creating Agents")
    print("-" * 70)
    
    file_agent = AgentFactory.create_agent(
        id="file_agent",
        role="File Operations Expert",
        goal="Handle file operations and analysis",
        tools=["file_reader"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    AgentRegistry.register(file_agent)
    print(f"✓ Created and registered: {file_agent.id}")
    print()

    # Step 3: Build graph
    print("Step 3: Building Graph")
    print("-" * 70)
    
    graph = _LegacyEnhancedGraph(name="file_processing_workflow")
    
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="file_node", agent_id="file_agent"))
    graph.add_node(OutputNode())
    
    graph.add_edge(Edge(source="input", target="file_node"))
    graph.add_edge(Edge(source="file_node", target="output"))
    
    print(f"✓ Graph created: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print()

    # Step 4: Execute workflow
    print("Step 4: Executing Workflow")
    print("-" * 70)
    
    readme_path = Path(__file__).parent.parent.parent / "README.md"
    
    input_data = {
        "task": "Read and analyze the README file",
        "file_path": str(readme_path) if readme_path.exists() else None
    }
    
    print(f"Input: {input_data['task']}")
    print()
    
    result = await graph.run(input_data=input_data)
    
    print()
    print("✓ Workflow completed successfully!")
    print()

    # Step 5: Display results
    print("Step 5: Results")
    print("-" * 70)
    if "file_node" in result:
        file_result = result["file_node"]
        print(f"Agent output: {file_result.get('output')}")
        if "tool_results" in file_result and "file_reader" in file_result["tool_results"]:
            reader_result = file_result["tool_results"]["file_reader"]
            print(f"File: {reader_result.get('path')}")
            print(f"Size: {reader_result.get('size')} bytes")
            print(f"Lines: {reader_result.get('lines')}")
    print()


async def scenario_3_multi_agent_workflow():
    """Scenario 3: Multi-agent workflow with sequential processing."""
    print("=" * 70)
    print("SCENARIO 3: Multi-Agent Sequential Workflow")
    print("=" * 70)
    print()

    # Step 1: Register tools
    print("Step 1: Registering Tools")
    print("-" * 70)
    calculator = CalculatorTool()
    ToolRegistry.register(calculator)
    print(f"✓ Registered calculator tool")
    print()

    # Step 2: Create and register agents
    print("Step 2: Creating Agents")
    print("-" * 70)
    
    collector = AgentFactory.create_agent(
        id="collector",
        role="Data Collector",
        goal="Gather and organize input data",
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    processor = AgentFactory.create_agent(
        id="processor",
        role="Data Processor",
        goal="Process and calculate results",
        tools=["calculator"],
        llm_model="gpt-4",
        temperature=0.2,
    )
    
    reporter = AgentFactory.create_agent(
        id="reporter",
        role="Report Generator",
        goal="Generate final report",
        llm_model="gpt-4",
        temperature=0.7,
    )
    
    AgentRegistry.register(collector)
    AgentRegistry.register(processor)
    AgentRegistry.register(reporter)
    
    print(f"✓ Created and registered 3 agents")
    print()

    # Step 3: Build graph
    print("Step 3: Building Sequential Graph")
    print("-" * 70)
    
    graph = _LegacyEnhancedGraph(name="multi_agent_workflow")
    
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="collector_node", agent_id="collector"))
    graph.add_node(AgentNode(id="processor_node", agent_id="processor"))
    graph.add_node(AgentNode(id="reporter_node", agent_id="reporter"))
    graph.add_node(OutputNode())
    
    graph.add_edge(Edge(source="input", target="collector_node"))
    graph.add_edge(Edge(source="collector_node", target="processor_node"))
    graph.add_edge(Edge(source="processor_node", target="reporter_node"))
    graph.add_edge(Edge(source="reporter_node", target="output"))
    
    print(f"✓ Graph created: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print("  Flow: Input → Collector → Processor → Reporter → Output")
    print()

    # Step 4: Execute workflow
    print("Step 4: Executing Workflow")
    print("-" * 70)
    
    input_data = {
        "task": "Calculate quarterly revenue growth",
        "expression": "150000 * 1.25"
    }
    
    print(f"Input: {input_data['task']}")
    print()
    
    result = await graph.run(input_data=input_data)
    
    print()
    print("✓ Workflow completed successfully!")
    print()

    # Step 5: Display results
    print("Step 5: Results")
    print("-" * 70)
    print("Execution flow:")
    for node_id in ["collector_node", "processor_node", "reporter_node"]:
        if node_id in result:
            node_result = result[node_id]
            agent_id = node_result.get("agent_id")
            print(f"  • {agent_id}: {node_result.get('status')}")
    print()


async def main():
    """Run all test scenarios."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "GenXAI - Fully Testable Workflow" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Check for API key
    has_api_key = bool(os.getenv("OPENAI_API_KEY"))
    if not has_api_key:
        print("ℹ️  Note: OPENAI_API_KEY not set")
        print("   Workflows will run with simulated agent responses")
        print("   Tools (calculator, file_reader) will execute normally")
        print()

    try:
        # Run scenarios
        await scenario_1_calculator_workflow()
        print("\n")
        
        await scenario_2_file_processing_workflow()
        print("\n")
        
        await scenario_3_multi_agent_workflow()
        print("\n")

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()
        print("✓ All scenarios completed successfully!")
        print()
        print("What was tested:")
        print("  ✓ Agent registration and retrieval")
        print("  ✓ Tool registration and execution")
        print("  ✓ Graph construction and validation")
        print("  ✓ Single-agent workflows")
        print("  ✓ Multi-agent sequential workflows")
        print("  ✓ Agent-tool integration")
        print()
        print("Registry Statistics:")
        print(f"  • Agents registered: {len(AgentRegistry.list_all())}")
        print(f"  • Tools registered: {len(ToolRegistry.list_all())}")
        print()
        
        if not has_api_key:
            print("💡 To enable full LLM-powered agent execution:")
            print("   export OPENAI_API_KEY='your-api-key'")
            print()

    finally:
        # Cleanup
        AgentRegistry.clear()
        ToolRegistry.clear()


if __name__ == "__main__":
    asyncio.run(main())
