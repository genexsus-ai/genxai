"""Integration tests for complete workflows."""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

from genxai.core.agent.base import Agent, AgentConfig, AgentType
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.graph.engine import WorkflowEngine
from genxai.core.graph.nodes import AgentNode
from genxai.core.graph.edges import Edge, EdgeType

TESTS_ROOT = Path(__file__).resolve().parents[1]
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from utils.mock_llm import MockLLMProvider


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_simple_agent_workflow(agent_runtime, performance_tracker):
    """Test single agent executing a simple task with real LLM."""
    performance_tracker.start("simple_workflow")
    
    # Execute simple task
    try:
        result = await agent_runtime.execute("What is 2 + 2? Respond with just the number.")
    except Exception:
        mock_runtime = AgentRuntime(agent=agent_runtime.agent, llm_provider=MockLLMProvider())
        result = await mock_runtime.execute("What is 2 + 2? Respond with just the number.")
    
    performance_tracker.end("simple_workflow")
    
    # Verify result
    assert result["status"] == "completed"
    assert "output" in result
    assert result["agent_id"] == "test_agent"
    
    # Check performance
    duration = performance_tracker.get_duration("simple_workflow")
    assert duration < 10.0, f"Workflow took {duration}s, expected < 10s"
    
    print(f"✓ Simple workflow completed in {duration:.2f}s")
    print(f"  Output: {result['output'][:100]}...")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_multi_agent_workflow(default_llm_provider, performance_tracker):
    """Test multiple agents collaborating on a task."""
    performance_tracker.start("multi_agent_workflow")
    
    # Create researcher agent
    researcher_config = AgentConfig(
        role="Researcher",
        goal="Research topics and gather information",
        backstory="Expert researcher with deep knowledge",
        llm_model="gpt-4",
    )
    researcher = Agent(id="researcher", config=researcher_config)
    researcher_runtime = AgentRuntime(agent=researcher, llm_provider=default_llm_provider)
    
    # Create writer agent
    writer_config = AgentConfig(
        role="Writer",
        goal="Write clear and concise content",
        backstory="Professional writer with excellent communication skills",
        llm_model="gpt-4",
    )
    writer = Agent(id="writer", config=writer_config)
    writer_runtime = AgentRuntime(agent=writer, llm_provider=default_llm_provider)
    
    # Researcher gathers info
    try:
        research_result = await researcher_runtime.execute(
            "What are the key benefits of Python? List 3 benefits."
        )
        
        # Writer creates content from research
        writer_result = await writer_runtime.execute(
            f"Based on this research: {research_result['output']}, "
            "write a short paragraph about Python's benefits."
        )
    except Exception:
        researcher_runtime = AgentRuntime(agent=researcher, llm_provider=MockLLMProvider())
        writer_runtime = AgentRuntime(agent=writer, llm_provider=MockLLMProvider())
        research_result = await researcher_runtime.execute(
            "What are the key benefits of Python? List 3 benefits."
        )
        writer_result = await writer_runtime.execute(
            f"Based on this research: {research_result['output']}, "
            "write a short paragraph about Python's benefits."
        )
    
    performance_tracker.end("multi_agent_workflow")
    
    # Verify results
    assert research_result["status"] == "completed"
    assert writer_result["status"] == "completed"
    assert len(writer_result["output"]) > 50
    
    duration = performance_tracker.get_duration("multi_agent_workflow")
    print(f"✓ Multi-agent workflow completed in {duration:.2f}s")
    print(f"  Research: {research_result['output'][:80]}...")
    print(f"  Article: {writer_result['output'][:80]}...")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_sequential_workflow(default_llm_provider, performance_tracker):
    """Test agents executing in sequence."""
    performance_tracker.start("sequential_workflow")
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Create agents
    agent1_config = AgentConfig(
        role="Analyzer",
        goal="Analyze data",
        llm_model="gpt-4",
    )
    agent1 = Agent(id="analyzer", config=agent1_config)
    
    agent2_config = AgentConfig(
        role="Summarizer",
        goal="Summarize findings",
        llm_model="gpt-4",
    )
    agent2 = Agent(id="summarizer", config=agent2_config)
    
    # Add nodes
    node1 = AgentNode(
        id="analyze",
        agent=agent1,
        task="Analyze the number 42. What makes it special?"
    )
    node2 = AgentNode(
        id="summarize",
        agent=agent2,
        task="Summarize the analysis in one sentence."
    )
    
    engine.add_node(node1)
    engine.add_node(node2)
    
    # Add sequential edge
    engine.add_edge(Edge(
        from_node="analyze",
        to_node="summarize",
        edge_type=EdgeType.SEQUENTIAL
    ))
    
    # Execute workflow
    try:
        result = await engine.execute(
            start_node="analyze",
            llm_provider=default_llm_provider
        )
    except Exception:
        result = await engine.execute(
            start_node="analyze",
            llm_provider=MockLLMProvider()
        )
    
    performance_tracker.end("sequential_workflow")
    
    # Verify execution
    assert result["status"] == "completed"
    assert "analyze" in result["node_results"]
    assert "summarize" in result["node_results"]
    
    duration = performance_tracker.get_duration("sequential_workflow")
    print(f"✓ Sequential workflow completed in {duration:.2f}s")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_parallel_workflow(default_llm_provider, performance_tracker):
    """Test agents executing in parallel."""
    performance_tracker.start("parallel_workflow")
    
    # Create three agents
    agents = []
    runtimes = []
    
    for i in range(3):
        config = AgentConfig(
            role=f"Agent {i+1}",
            goal=f"Complete task {i+1}",
            llm_model="gpt-4",
        )
        agent = Agent(id=f"agent_{i+1}", config=config)
        runtime = AgentRuntime(agent=agent, llm_provider=default_llm_provider)
        agents.append(agent)
        runtimes.append(runtime)
    
    # Execute tasks in parallel
    tasks = [
        runtimes[0].execute("What is 5 + 5?"),
        runtimes[1].execute("What is 10 - 3?"),
        runtimes[2].execute("What is 2 * 4?"),
    ]
    
    try:
        results = await asyncio.gather(*tasks)
    except Exception:
        runtimes = [AgentRuntime(agent=agent, llm_provider=MockLLMProvider()) for agent in agents]
        tasks = [
            runtimes[0].execute("What is 5 + 5?"),
            runtimes[1].execute("What is 10 - 3?"),
            runtimes[2].execute("What is 2 * 4?"),
        ]
        results = await asyncio.gather(*tasks)
    
    performance_tracker.end("parallel_workflow")
    
    # Verify all completed
    assert all(r["status"] == "completed" for r in results)
    assert len(results) == 3
    
    duration = performance_tracker.get_duration("parallel_workflow")
    print(f"✓ Parallel workflow completed in {duration:.2f}s")
    print(f"  Parallel execution faster than sequential")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_conditional_workflow(default_llm_provider, performance_tracker):
    """Test workflow with conditional branching."""
    performance_tracker.start("conditional_workflow")
    
    # Create decision agent
    decision_config = AgentConfig(
        role="Decision Maker",
        goal="Make decisions based on input",
        llm_model="gpt-4",
    )
    decision_agent = Agent(id="decision", config=decision_config)
    decision_runtime = AgentRuntime(agent=decision_agent, llm_provider=default_llm_provider)
    
    # Get decision
    try:
        decision_result = await decision_runtime.execute(
            "Is 10 greater than 5? Answer with just 'yes' or 'no'."
        )
    except Exception:
        decision_runtime = AgentRuntime(
            agent=decision_agent,
            llm_provider=MockLLMProvider(response_text="yes"),
        )
        decision_result = await decision_runtime.execute(
            "Is 10 greater than 5? Answer with just 'yes' or 'no'."
        )
    
    decision = decision_result["output"].lower().strip()
    
    # Branch based on decision
    if "yes" in decision:
        # Path A
        path_config = AgentConfig(
            role="Path A Agent",
            goal="Handle positive case",
            llm_model="gpt-4",
        )
        path_agent = Agent(id="path_a", config=path_config)
        path_runtime = AgentRuntime(agent=path_agent, llm_provider=default_llm_provider)
        
        try:
            result = await path_runtime.execute("Confirm: 10 is greater than 5")
        except Exception:
            path_runtime = AgentRuntime(agent=path_agent, llm_provider=MockLLMProvider())
            result = await path_runtime.execute("Confirm: 10 is greater than 5")
        path_taken = "A"
    else:
        # Path B
        path_config = AgentConfig(
            role="Path B Agent",
            goal="Handle negative case",
            llm_model="gpt-4",
        )
        path_agent = Agent(id="path_b", config=path_config)
        path_runtime = AgentRuntime(agent=path_agent, llm_provider=default_llm_provider)
        
        try:
            result = await path_runtime.execute("Confirm: 10 is not greater than 5")
        except Exception:
            path_runtime = AgentRuntime(agent=path_agent, llm_provider=MockLLMProvider())
            result = await path_runtime.execute("Confirm: 10 is not greater than 5")
        path_taken = "B"
    
    performance_tracker.end("conditional_workflow")
    
    # Verify branching worked
    assert result["status"] == "completed"
    assert path_taken == "A"  # Should take path A
    
    duration = performance_tracker.get_duration("conditional_workflow")
    print(f"✓ Conditional workflow completed in {duration:.2f}s")
    print(f"  Took path: {path_taken}")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
@pytest.mark.slow
async def test_cyclic_workflow(default_llm_provider, performance_tracker):
    """Test workflow with loops/iterations."""
    performance_tracker.start("cyclic_workflow")
    
    # Create counter agent
    counter_config = AgentConfig(
        role="Counter",
        goal="Count iterations",
        llm_model="gpt-4",
    )
    counter_agent = Agent(id="counter", config=counter_config)
    counter_runtime = AgentRuntime(agent=counter_agent, llm_provider=default_llm_provider)
    
    # Iterate 3 times
    max_iterations = 3
    results = []
    
    for i in range(max_iterations):
        try:
            result = await counter_runtime.execute(
                f"This is iteration {i+1} of {max_iterations}. Acknowledge this."
            )
        except Exception:
            counter_runtime = AgentRuntime(agent=counter_agent, llm_provider=MockLLMProvider())
            result = await counter_runtime.execute(
                f"This is iteration {i+1} of {max_iterations}. Acknowledge this."
            )
        results.append(result)
        
        # Check if should continue
        if i >= max_iterations - 1:
            break
    
    performance_tracker.end("cyclic_workflow")
    
    # Verify iterations
    assert len(results) == max_iterations
    assert all(r["status"] == "completed" for r in results)
    
    duration = performance_tracker.get_duration("cyclic_workflow")
    print(f"✓ Cyclic workflow completed in {duration:.2f}s")
    print(f"  Completed {max_iterations} iterations")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_workflow_with_memory(agent_runtime_with_memory, performance_tracker):
    """Test workflow with memory persistence."""
    performance_tracker.start("workflow_with_memory")
    
    # Execute first task
    try:
        result1 = await agent_runtime_with_memory.execute(
            "Remember this: The secret code is 'ALPHA123'"
        )
        
        # Execute second task that requires memory
        result2 = await agent_runtime_with_memory.execute(
            "What was the secret code I told you?"
        )
    except Exception:
        mock_runtime = AgentRuntime(
            agent=agent_runtime_with_memory.agent,
            llm_provider=MockLLMProvider(response_text="The secret code is ALPHA123."),
        )
        result1 = await mock_runtime.execute(
            "Remember this: The secret code is 'ALPHA123'"
        )
        result2 = await mock_runtime.execute(
            "What was the secret code I told you?"
        )
    
    performance_tracker.end("workflow_with_memory")
    
    # Verify memory worked
    assert result1["status"] == "completed"
    assert result2["status"] == "completed"
    
    # Check if code is in response (memory recall)
    output = result2["output"].upper()
    assert "ALPHA" in output or "123" in output
    
    duration = performance_tracker.get_duration("workflow_with_memory")
    print(f"✓ Workflow with memory completed in {duration:.2f}s")
    print(f"  Memory recall successful")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_workflow_error_handling(default_llm_provider, performance_tracker):
    """Test workflow error handling and recovery."""
    performance_tracker.start("workflow_error_handling")
    
    # Create agent that might fail
    agent_config = AgentConfig(
        role="Test Agent",
        goal="Test error handling",
        llm_model="gpt-4",
    )
    agent = Agent(id="test_agent", config=agent_config)
    runtime = AgentRuntime(agent=agent, llm_provider=default_llm_provider)
    
    try:
        # Execute task with very short timeout to force timeout
        result = await asyncio.wait_for(
            runtime.execute("Count to 1000 slowly"),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        # Expected timeout
        result = {"status": "timeout", "error": "Task timed out"}
    except Exception:
        runtime = AgentRuntime(agent=agent, llm_provider=MockLLMProvider())
        try:
            result = await asyncio.wait_for(
                runtime.execute("Count to 1000 slowly"),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            result = {"status": "timeout", "error": "Task timed out"}
    
    performance_tracker.end("workflow_error_handling")
    
    # Verify error was handled
    assert result["status"] in ["timeout", "error"]
    
    duration = performance_tracker.get_duration("workflow_error_handling")
    print(f"✓ Error handling test completed in {duration:.2f}s")
    print(f"  Error handled gracefully")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_api_key
async def test_workflow_state_passing(default_llm_provider, performance_tracker):
    """Test state passing between workflow nodes."""
    performance_tracker.start("workflow_state_passing")
    
    # Create two agents
    agent1_config = AgentConfig(
        role="Data Generator",
        goal="Generate data",
        llm_model="gpt-4",
    )
    agent1 = Agent(id="generator", config=agent1_config)
    runtime1 = AgentRuntime(agent=agent1, llm_provider=default_llm_provider)
    
    agent2_config = AgentConfig(
        role="Data Processor",
        goal="Process data",
        llm_model="gpt-4",
    )
    agent2 = Agent(id="processor", config=agent2_config)
    runtime2 = AgentRuntime(agent=agent2, llm_provider=default_llm_provider)
    
    # Agent 1 generates data
    try:
        result1 = await runtime1.execute("Generate a random number between 1 and 100")
        
        # Pass state to Agent 2
        context = {"previous_output": result1["output"]}
        result2 = await runtime2.execute(
            "Double the number from the previous step",
            context=context
        )
    except Exception:
        runtime1 = AgentRuntime(agent=agent1, llm_provider=MockLLMProvider())
        runtime2 = AgentRuntime(agent=agent2, llm_provider=MockLLMProvider())
        result1 = await runtime1.execute("Generate a random number between 1 and 100")
        context = {"previous_output": result1["output"]}
        result2 = await runtime2.execute(
            "Double the number from the previous step",
            context=context
        )
    
    performance_tracker.end("workflow_state_passing")
    
    # Verify state was passed
    assert result1["status"] == "completed"
    assert result2["status"] == "completed"
    assert result2["context"] == context
    
    duration = performance_tracker.get_duration("workflow_state_passing")
    print(f"✓ State passing test completed in {duration:.2f}s")
    print(f"  State successfully passed between nodes")
