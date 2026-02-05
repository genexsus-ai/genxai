"""Example: Agent using tools automatically."""

import asyncio
from genxai.core.agent.base import Agent, AgentConfig
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry


async def main():
    """Run agent with tools example."""
    
    # Create agent configuration
    config = AgentConfig(
        role="Data Analyst",
        goal="Analyze data and provide insights",
        backstory="Expert in data analysis with access to various tools",
        llm_model="gpt-4",
        llm_temperature=0.7,
        tools=["web_scraper", "json_processor", "text_analyzer"],
    )
    
    # Create agent
    agent = Agent(id="analyst", config=config)
    
    # Create runtime
    runtime = AgentRuntime(agent=agent)
    
    # Load tools from registry
    registry = ToolRegistry()
    tools = {
        "web_scraper": registry.get_tool("web_scraper"),
        "json_processor": registry.get_tool("json_processor"),
        "text_analyzer": registry.get_tool("text_analyzer"),
    }
    runtime.set_tools(tools)
    
    # Execute task that requires tools
    task = """
    Analyze the following JSON data and provide insights:
    {"sales": [100, 150, 200, 175, 225], "region": "North America"}
    
    Calculate the average and identify trends.
    """
    
    print("Executing agent with tools...")
    result = await runtime.execute(task)
    
    print(f"\nAgent: {result['agent_id']}")
    print(f"Status: {result['status']}")
    print(f"Output: {result['output']}")
    print(f"Tokens used: {result['tokens_used']}")
    print(f"Execution time: {result['execution_time']:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
