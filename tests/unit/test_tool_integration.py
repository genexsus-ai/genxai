"""Unit tests for tool integration in AgentRuntime."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from genxai.core.agent.base import Agent, AgentConfig
from genxai.core.agent.runtime import AgentRuntime
from genxai.llm.base import LLMResponse


class MockTool:
    """Mock tool for testing."""
    
    def __init__(self, return_value: Any = "tool_result"):
        self.return_value = return_value
        self.call_count = 0
        self.calls = []
        self.metadata = Mock(description="Mock tool for testing")
    
    async def execute(self, **kwargs):
        """Mock execute method."""
        self.call_count += 1
        self.calls.append(kwargs)
        return self.return_value


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Mock generate method."""
        response = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return LLMResponse(
            content=response,
            model="gpt-4",
            usage={"total_tokens": 100},
            finish_reason="stop",
        )


@pytest.fixture
def agent():
    """Create test agent."""
    config = AgentConfig(
        role="Test Agent",
        goal="Test goal",
        llm_model="gpt-4",
        tools=["tool1", "tool2"],
    )
    return Agent(id="test_agent", config=config)


# ==================== Tool Call Parsing Tests ====================

def test_parse_json_tool_calls():
    """Test parsing JSON format tool calls."""
    config = AgentConfig(role="Test", goal="Test", llm_model="gpt-4")
    agent = Agent(id="test", config=config)
    runtime = AgentRuntime(agent=agent)
    
    response = '''
    I will use the calculator tool.
    {"name": "calculator", "arguments": {"operation": "add", "a": 5, "b": 3}}
    '''
    
    tool_calls = runtime._parse_tool_calls(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "calculator"
    assert tool_calls[0]["arguments"]["operation"] == "add"


def test_parse_text_tool_calls():
    """Test parsing text format tool calls."""
    config = AgentConfig(role="Test", goal="Test", llm_model="gpt-4")
    agent = Agent(id="test", config=config)
    runtime = AgentRuntime(agent=agent)
    
    response = '''
    I will search for information.
    USE_TOOL: web_scraper(url="https://example.com", selector="div.content")
    '''
    
    tool_calls = runtime._parse_tool_calls(response)
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "web_scraper"
    assert tool_calls[0]["arguments"]["url"] == "https://example.com"


def test_parse_multiple_tool_calls():
    """Test parsing multiple tool calls."""
    config = AgentConfig(role="Test", goal="Test", llm_model="gpt-4")
    agent = Agent(id="test", config=config)
    runtime = AgentRuntime(agent=agent)
    
    response = '''
    {"name": "tool1", "arguments": {"arg1": "value1"}}
    USE_TOOL: tool2(arg2="value2")
    '''
    
    tool_calls = runtime._parse_tool_calls(response)
    
    assert len(tool_calls) == 2
    assert tool_calls[0]["name"] == "tool1"
    assert tool_calls[1]["name"] == "tool2"


def test_parse_no_tool_calls():
    """Test parsing response with no tool calls."""
    config = AgentConfig(role="Test", goal="Test", llm_model="gpt-4")
    agent = Agent(id="test", config=config)
    runtime = AgentRuntime(agent=agent)
    
    response = "This is a regular response without any tool calls."
    
    tool_calls = runtime._parse_tool_calls(response)
    
    assert len(tool_calls) == 0


# ==================== Tool Execution Tests ====================

@pytest.mark.asyncio
async def test_execute_tool_success(agent):
    """Test successful tool execution."""
    mock_tool = MockTool(return_value="success")
    runtime = AgentRuntime(agent=agent)
    runtime.set_tools({"test_tool": mock_tool})
    
    tool_call = {"name": "test_tool", "arguments": {"arg1": "value1"}}
    result = await runtime._execute_tool(tool_call, {})
    
    assert result == "success"
    assert mock_tool.call_count == 1
    assert mock_tool.calls[0] == {"arg1": "value1"}


@pytest.mark.asyncio
async def test_execute_tool_not_found(agent):
    """Test tool execution with non-existent tool."""
    runtime = AgentRuntime(agent=agent)
    runtime.set_tools({})
    
    tool_call = {"name": "nonexistent", "arguments": {}}
    
    with pytest.raises(ValueError, match="not found"):
        await runtime._execute_tool(tool_call, {})


@pytest.mark.asyncio
async def test_execute_tool_with_error(agent):
    """Test tool execution that raises error."""
    mock_tool = Mock()
    mock_tool.execute = Mock(side_effect=RuntimeError("Tool error"))
    
    runtime = AgentRuntime(agent=agent)
    runtime.set_tools({"failing_tool": mock_tool})
    
    tool_call = {"name": "failing_tool", "arguments": {}}
    
    with pytest.raises(RuntimeError, match="Tool error"):
        await runtime._execute_tool(tool_call, {})


@pytest.mark.asyncio
async def test_execute_async_tool(agent):
    """Test execution of async tool."""
    mock_tool = MockTool(return_value="async_result")
    runtime = AgentRuntime(agent=agent)
    runtime.set_tools({"async_tool": mock_tool})
    
    tool_call = {"name": "async_tool", "arguments": {"key": "value"}}
    result = await runtime._execute_tool(tool_call, {})
    
    assert result == "async_result"


# ==================== Tool Chaining Tests ====================

@pytest.mark.asyncio
async def test_tool_chaining(agent):
    """Test sequential tool chaining."""
    # First response has tool call, second response is final
    mock_provider = MockLLMProvider([
        '{"name": "tool1", "arguments": {"arg": "value"}}',
        "Final response after tool execution"
    ])
    
    mock_tool = MockTool(return_value="tool1_result")
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": mock_tool})
    
    result = await runtime.execute("Test task")
    
    assert result["status"] == "completed"
    assert mock_tool.call_count == 1


@pytest.mark.asyncio
async def test_tool_chaining_max_iterations(agent):
    """Test tool chaining stops at max iterations."""
    # Always return tool calls
    mock_provider = MockLLMProvider([
        '{"name": "tool1", "arguments": {}}' for _ in range(10)
    ])
    
    mock_tool = MockTool(return_value="result")
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": mock_tool})
    
    result = await runtime.execute("Test task")
    
    # Should stop at max_iterations (5)
    assert mock_tool.call_count <= 5


@pytest.mark.asyncio
async def test_tool_chaining_context_update(agent):
    """Test that tool results update context for chaining."""
    responses = [
        '{"name": "tool1", "arguments": {}}',
        '{"name": "tool2", "arguments": {}}',
        "Final response"
    ]
    mock_provider = MockLLMProvider(responses)
    
    tool1 = MockTool(return_value="result1")
    tool2 = MockTool(return_value="result2")
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": tool1, "tool2": tool2})
    
    context = {}
    result = await runtime.execute("Test task", context=context)
    
    # Context should have tool results
    assert "tool_result_tool1" in context
    assert "tool_result_tool2" in context


# ==================== Tool Result Formatting Tests ====================

@pytest.mark.asyncio
async def test_format_tool_results_success(agent):
    """Test formatting successful tool results."""
    mock_provider = MockLLMProvider(["Formatted response"])
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    tool_results = [
        {"tool": "tool1", "success": True, "result": "result1"},
        {"tool": "tool2", "success": True, "result": "result2"},
    ]
    
    formatted = await runtime._format_tool_results("Original", tool_results)
    
    assert "Formatted response" in formatted


@pytest.mark.asyncio
async def test_format_tool_results_with_errors(agent):
    """Test formatting tool results with errors."""
    mock_provider = MockLLMProvider(["Response with errors"])
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    tool_results = [
        {"tool": "tool1", "success": True, "result": "result1"},
        {"tool": "tool2", "success": False, "error": "Tool failed"},
    ]
    
    formatted = await runtime._format_tool_results("Original", tool_results)
    
    assert "Response with errors" in formatted


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_full_tool_integration(agent):
    """Test full tool integration flow."""
    responses = [
        'I will use tool1. {"name": "tool1", "arguments": {"key": "value"}}',
        "Based on the tool result, here is my final answer."
    ]
    mock_provider = MockLLMProvider(responses)
    
    mock_tool = MockTool(return_value="tool_result")
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": mock_tool})
    
    result = await runtime.execute("Test task with tools")
    
    assert result["status"] == "completed"
    assert mock_tool.call_count == 1
    assert "final answer" in result["output"].lower()


@pytest.mark.asyncio
async def test_tool_integration_no_tools_needed(agent):
    """Test execution when no tools are needed."""
    mock_provider = MockLLMProvider(["Direct response without tools"])
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": MockTool()})
    
    result = await runtime.execute("Simple task")
    
    assert result["status"] == "completed"
    assert "Direct response" in result["output"]


@pytest.mark.asyncio
async def test_tool_integration_with_multiple_tools(agent):
    """Test using multiple tools in sequence."""
    responses = [
        '{"name": "tool1", "arguments": {}}',
        '{"name": "tool2", "arguments": {}}',
        "Final response using both tools"
    ]
    mock_provider = MockLLMProvider(responses)
    
    tool1 = MockTool(return_value="result1")
    tool2 = MockTool(return_value="result2")
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": tool1, "tool2": tool2})
    
    result = await runtime.execute("Task requiring multiple tools")
    
    assert result["status"] == "completed"
    assert tool1.call_count == 1
    assert tool2.call_count == 1


# ==================== Error Handling Tests ====================

@pytest.mark.asyncio
async def test_tool_error_handling(agent):
    """Test graceful handling of tool errors."""
    responses = [
        '{"name": "failing_tool", "arguments": {}}',
        "Response despite tool failure"
    ]
    mock_provider = MockLLMProvider(responses)
    
    failing_tool = Mock()
    failing_tool.execute = Mock(side_effect=RuntimeError("Tool failed"))
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"failing_tool": failing_tool})
    
    result = await runtime.execute("Task with failing tool")
    
    # Should complete despite tool failure
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_partial_tool_failure(agent):
    """Test handling when some tools succeed and some fail."""
    responses = [
        '{"name": "tool1", "arguments": {}} {"name": "tool2", "arguments": {}}',
        "Response with partial results"
    ]
    mock_provider = MockLLMProvider(responses)
    
    tool1 = MockTool(return_value="success")
    tool2 = Mock()
    tool2.execute = Mock(side_effect=RuntimeError("Failed"))
    
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    runtime.set_tools({"tool1": tool1, "tool2": tool2})
    
    result = await runtime.execute("Task with partial failure")
    
    assert result["status"] == "completed"
    assert tool1.call_count == 1
