"""Example demonstrating LLM-powered agents in GenXAI.

This example shows how to create and execute agents with real LLM integration.
Requires OPENAI_API_KEY environment variable to be set.
"""

import asyncio
import os
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime


async def simple_agent_example():
    """Simple example of an agent answering a question."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Agent")
    print("=" * 60)
    
    # Create an agent
    agent = AgentFactory.create_agent(
        id="assistant",
        role="Helpful Assistant",
        goal="Answer questions accurately and concisely",
        llm_model="gpt-3.5-turbo",
        temperature=0.7,
    )
    
    # Create runtime
    runtime = AgentRuntime(agent=agent)
    
    # Execute task
    print("\nTask: What is the capital of France?")
    result = await runtime.execute(
        task="What is the capital of France? Answer in one sentence."
    )
    
    print(f"\nAgent Response: {result['output']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Tokens Used: {agent._total_tokens}")


async def agent_with_personality():
    """Example of an agent with a specific personality."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Agent with Personality")
    print("=" * 60)
    
    # Create a pirate agent
    agent = AgentFactory.create_agent(
        id="pirate_captain",
        role="Pirate Captain",
        goal="Speak like a pirate and tell stories",
        backstory="You are Captain Blackbeard, a legendary pirate who sailed the Caribbean seas for 20 years.",
        llm_model="gpt-3.5-turbo",
        temperature=0.9,  # Higher temperature for more creative responses
    )
    
    runtime = AgentRuntime(agent=agent)
    
    print("\nTask: Tell me about your greatest treasure hunt.")
    result = await runtime.execute(
        task="Tell me about your greatest treasure hunt in 2-3 sentences."
    )
    
    print(f"\nPirate Captain: {result['output']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")


async def deliberative_agent_example():
    """Example of a deliberative agent that plans before acting."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Deliberative Agent")
    print("=" * 60)
    
    # Create a strategic planner agent
    agent = AgentFactory.create_agent(
        id="strategic_planner",
        role="Strategic Planner",
        goal="Create detailed, well-thought-out plans",
        agent_type="deliberative",  # This adds planning instructions
        llm_model="gpt-3.5-turbo",
        temperature=0.5,
    )
    
    runtime = AgentRuntime(agent=agent)
    
    print("\nTask: Plan a product launch for a new mobile app.")
    result = await runtime.execute(
        task="Create a brief plan for launching a new mobile app. Include 3-4 key steps."
    )
    
    print(f"\nStrategic Plan:\n{result['output']}")
    print(f"\nExecution Time: {result['execution_time']:.2f}s")


async def batch_execution_example():
    """Example of executing multiple tasks in parallel."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Batch Execution")
    print("=" * 60)
    
    # Create a math tutor agent
    agent = AgentFactory.create_agent(
        id="math_tutor",
        role="Math Tutor",
        goal="Solve math problems and explain solutions",
        llm_model="gpt-3.5-turbo",
        temperature=0.3,  # Lower temperature for more consistent math
    )
    
    runtime = AgentRuntime(agent=agent)
    
    # Execute multiple tasks in parallel
    tasks = [
        "What is 15 * 23? Show your work.",
        "What is the square root of 144?",
        "If a train travels 60 mph for 2.5 hours, how far does it go?",
    ]
    
    print("\nExecuting 3 math problems in parallel...")
    results = await runtime.batch_execute(tasks)
    
    for i, (task, result) in enumerate(zip(tasks, results), 1):
        print(f"\nProblem {i}: {task}")
        if "output" in result:
            print(f"Solution: {result['output']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")


async def agent_with_context():
    """Example of an agent using context from previous interactions."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Agent with Context")
    print("=" * 60)
    
    # Create a customer service agent
    agent = AgentFactory.create_agent(
        id="customer_service",
        role="Customer Service Representative",
        goal="Help customers with their issues professionally",
        backstory="You work for TechCorp, a software company that sells productivity tools.",
        llm_model="gpt-3.5-turbo",
        temperature=0.7,
    )
    
    runtime = AgentRuntime(agent=agent)
    
    # First interaction
    print("\nCustomer: My software won't start after the update.")
    result1 = await runtime.execute(
        task="A customer says: 'My software won't start after the update.' Respond helpfully.",
        context={"customer_name": "John", "product": "TechCorp Pro"}
    )
    print(f"Agent: {result1['output']}")
    
    # Second interaction with context from first
    print("\nCustomer: I tried that but it still doesn't work.")
    result2 = await runtime.execute(
        task="Customer says: 'I tried that but it still doesn't work.' Provide next steps.",
        context={
            "customer_name": "John",
            "product": "TechCorp Pro",
            "previous_suggestion": result1['output'][:100]  # Include part of previous response
        }
    )
    print(f"Agent: {result2['output']}")


async def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print("\n🚀 GenXAI LLM-Powered Agent Examples")
    print("=" * 60)
    
    try:
        # Run examples
        await simple_agent_example()
        await agent_with_personality()
        await deliberative_agent_example()
        await batch_execution_example()
        await agent_with_context()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
