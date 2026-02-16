"""Unit tests for AgentRuntime."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from genxai.core.agent.base import Agent, AgentConfig, AgentType
from genxai.core.agent.runtime import AgentRuntime, AgentExecutionError
from genxai.llm.base import LLMResponse


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_content: str = "Mock response", fail_count: int = 0):
        """Initialize mock provider.
        
        Args:
            response_content: Content to return
            fail_count: Number of times to fail before succeeding
        """
        self.response_content = response_content
        self.fail_count = fail_count
        self.call_count = 0
        self.calls = []

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Mock generate method."""
        self.call_count += 1
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        
        # Fail for first N calls if fail_count set
        if self.call_count <= self.fail_count:
            raise RuntimeError(f"Mock LLM failure {self.call_count}")
        
        return LLMResponse(
            content=self.response_content,
            model="gpt-4",
            usage={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
            finish_reason="stop",
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        **kwargs: Any
    ):
        """Mock streaming generate method."""
        chunks = self.response_content.split()
        for chunk in chunks:
            yield chunk + " "


class MockMemory:
    """Mock memory system for testing."""

    def __init__(self):
        """Initialize mock memory."""
        self.stored_items = []
        self.recent_memories = []

    def store(self, content: Any, memory_type: Any, importance: float, tags: list, metadata: dict) -> str:
        """Mock store method."""
        memory_id = f"mem_{len(self.stored_items)}"
        self.stored_items.append({
            "id": memory_id,
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags,
            "metadata": metadata,
        })
        return memory_id

    def retrieve_recent(self, limit: int = 5) -> list:
        """Mock retrieve_recent method."""
        return self.recent_memories[:limit]
    
    async def get_short_term_context(self, max_tokens: int = 2000) -> str:
        """Mock get_short_term_context method."""
        if not self.recent_memories:
            return ""
        
        context_parts = ["Recent context:"]
        for memory in self.recent_memories:
            if hasattr(memory, 'content') and isinstance(memory.content, dict):
                task = memory.content.get("task", "")
                response = memory.content.get("response", "")
                context_parts.append(f"- Task: {task}")
                context_parts.append(f"  Response: {response}")
        
        return "\n".join(context_parts)
    
    async def add_to_short_term(self, content: Any, metadata: dict) -> str:
        """Mock add_to_short_term method."""
        memory_id = f"mem_{len(self.stored_items)}"
        self.stored_items.append({
            "id": memory_id,
            "content": content,
            "metadata": metadata,
        })
        return memory_id


class MockRollingMemory:
    """Mock memory with rolling-summary APIs."""

    def __init__(self, older_context: str = "", prompt_context: str = "") -> None:
        self._older_context = older_context
        self._prompt_context = prompt_context
        self.summary = ""
        self.pruned_to = None
        self.config = type(
            "Cfg",
            (),
            {
                "rolling_summary_enabled": True,
                "short_term_window_size": 2,
                "rolling_summary_trigger_tokens": 5,
            },
        )()

    async def get_older_context_for_summary(self, keep_recent: int = 2) -> str:
        return self._older_context

    def get_rolling_summary(self) -> str:
        return self.summary

    def set_rolling_summary(self, summary: str) -> None:
        self.summary = summary

    def prune_short_term_to_window(self, keep_recent: int = 2) -> int:
        self.pruned_to = keep_recent
        return 1

    async def build_prompt_memory_context(self, window_size: int = 2, max_tokens: int = 2000) -> str:
        return self._prompt_context

    async def get_short_term_context(self, max_tokens: int = 2000) -> str:
        return "fallback"


@pytest.fixture
def agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        role="Test Agent",
        goal="Test goal",
        backstory="Test backstory",
        llm_model="gpt-4",
        llm_temperature=0.7,
        tools=["tool1", "tool2"],
    )


@pytest.fixture
def agent(agent_config):
    """Create test agent."""
    return Agent(id="test_agent", config=agent_config)


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def runtime(agent, mock_llm_provider):
    """Create agent runtime with mock provider."""
    runtime = AgentRuntime(agent=agent, llm_provider=mock_llm_provider)
    return runtime


# ==================== Basic Execution Tests ====================

@pytest.mark.asyncio
async def test_agent_runtime_initialization(agent, mock_llm_provider):
    """Test agent runtime initialization."""
    runtime = AgentRuntime(agent=agent, llm_provider=mock_llm_provider)
    
    assert runtime.agent == agent
    assert runtime._llm_provider == mock_llm_provider
    assert runtime._tools == {}
    assert runtime._memory is not None  # Memory system is initialized by default
    assert runtime._memory.agent_id == agent.id


@pytest.mark.asyncio
async def test_execute_basic_task(runtime):
    """Test basic task execution."""
    result = await runtime.execute("Test task")
    
    assert result["status"] == "completed"
    assert result["agent_id"] == "test_agent"
    assert result["task"] == "Test task"
    assert "output" in result
    assert "execution_time" in result
    assert result["output"] == "Mock response"


@pytest.mark.asyncio
async def test_execute_with_context(runtime):
    """Test execution with context dictionary."""
    context = {"key": "value", "number": 42}
    result = await runtime.execute("Test task", context=context)
    
    assert result["status"] == "completed"
    assert result["context"] == context


@pytest.mark.asyncio
async def test_execute_timeout(runtime):
    """Test execution timeout handling."""
    # Create a slow mock provider
    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(2)
        return LLMResponse(content="Slow response", model="gpt-4", usage={"total_tokens": 100})
    
    runtime._llm_provider.generate = slow_generate
    
    with pytest.raises(asyncio.TimeoutError):
        await runtime.execute("Test task", timeout=0.1)


# ==================== Memory Integration Tests ====================

@pytest.mark.asyncio
async def test_execute_with_memory(runtime):
    """Test execution with memory context."""
    # Set up mock memory
    mock_memory = MockMemory()
    mock_memory.recent_memories = [
        Mock(content={"task": "Previous task", "response": "Previous response"})
    ]
    runtime.set_memory(mock_memory)
    
    result = await runtime.execute("Test task")
    
    assert result["status"] == "completed"
    assert len(mock_memory.stored_items) > 0


@pytest.mark.asyncio
async def test_memory_context_formatting(runtime):
    """Test memory context string formatting."""
    mock_memory = MockMemory()
    mock_memory.recent_memories = [
        Mock(content={"task": "Task 1", "response": "Response 1"}),
        Mock(content={"task": "Task 2", "response": "Response 2"}),
    ]
    runtime.set_memory(mock_memory)
    
    context = await runtime.get_memory_context(limit=2)
    
    assert "Recent context:" in context
    assert "Task 1" in context
    assert "Task 2" in context


@pytest.mark.asyncio
async def test_memory_update_after_execution(runtime):
    """Test memory storage after execution."""
    mock_memory = MockMemory()
    runtime.set_memory(mock_memory)
    
    await runtime.execute("Test task")
    
    assert len(mock_memory.stored_items) == 1
    stored = mock_memory.stored_items[0]
    assert stored["content"]["task"] == "Test task"
    assert stored["content"]["response"] == "Mock response"


@pytest.mark.asyncio
async def test_get_memory_context_prefers_prompt_context_builder(runtime):
    """Runtime should use memory.build_prompt_memory_context when available."""
    rolling_memory = MockRollingMemory(
        older_context="",  # no summary refresh needed
        prompt_context="Conversation summary:\nshort summary\n\nRecent turns:\n- latest",
    )
    runtime.set_memory(rolling_memory)

    context = await runtime.get_memory_context(limit=2)
    assert "Conversation summary" in context
    assert "latest" in context


@pytest.mark.asyncio
async def test_refresh_rolling_summary_when_threshold_exceeded(runtime):
    """Runtime should summarize older context and prune memory window."""
    long_older_context = "Older turns:\n" + ("x" * 200)
    rolling_memory = MockRollingMemory(
        older_context=long_older_context,
        prompt_context="Recent turns:\n- kept",
    )
    runtime.set_memory(rolling_memory)

    await runtime.get_memory_context(limit=2)

    assert rolling_memory.summary != ""
    assert rolling_memory.pruned_to == 2


# ==================== Retry Logic Tests ====================

@pytest.mark.asyncio
async def test_retry_on_llm_failure(agent):
    """Test exponential backoff retry on LLM failure."""
    # Create provider that fails twice then succeeds
    mock_provider = MockLLMProvider(fail_count=2)
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    result = await runtime.execute("Test task")
    
    assert result["status"] == "completed"
    assert mock_provider.call_count == 3  # Failed twice, succeeded on third


@pytest.mark.asyncio
async def test_retry_exhaustion(agent):
    """Test failure after max retries."""
    # Create provider that always fails
    mock_provider = MockLLMProvider(fail_count=10)
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    with pytest.raises(AgentExecutionError):
        await runtime.execute("Test task")
    
    assert mock_provider.call_count == 3  # Default max_retries


@pytest.mark.asyncio
async def test_retry_success_on_second_attempt(agent):
    """Test successful retry on second attempt."""
    mock_provider = MockLLMProvider(fail_count=1)
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    result = await runtime.execute("Test task")
    
    assert result["status"] == "completed"
    assert mock_provider.call_count == 2


# ==================== Streaming Tests ====================

@pytest.mark.asyncio
async def test_stream_execute(runtime):
    """Test streaming execution."""
    chunks = []
    async for chunk in runtime.stream_execute("Test task"):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    full_response = "".join(chunks)
    assert "Mock" in full_response
    assert "response" in full_response


@pytest.mark.asyncio
async def test_stream_memory_update(runtime):
    """Test memory update after streaming."""
    mock_memory = MockMemory()
    runtime.set_memory(mock_memory)
    
    chunks = []
    async for chunk in runtime.stream_execute("Test task"):
        chunks.append(chunk)
    
    # Memory should be updated with full response
    assert len(mock_memory.stored_items) == 1


# ==================== Prompt Building Tests ====================

def test_build_prompt_basic(runtime):
    """Test basic prompt construction."""
    prompt = runtime._build_prompt("Test task", {})
    
    assert "Task: Test task" in prompt


def test_build_prompt_with_tools(runtime):
    """Test prompt with tool descriptions."""
    # Set up mock tools
    mock_tool = Mock()
    mock_tool.metadata = Mock(description="Test tool description")
    runtime.set_tools({"tool1": mock_tool})
    
    prompt = runtime._build_prompt("Test task", {})
    
    assert "Available tools:" in prompt
    assert "tool1" in prompt


def test_build_system_prompt(runtime):
    """Test system prompt construction."""
    system_prompt = runtime._build_system_prompt()
    
    assert "Test Agent" in system_prompt
    assert "Test goal" in system_prompt
    assert "Test backstory" in system_prompt


def test_build_prompt_agent_types():
    """Test agent-type specific instructions."""
    # Test deliberative agent
    config = AgentConfig(
        role="Planner",
        goal="Plan tasks",
        agent_type=AgentType.DELIBERATIVE,
        llm_model="gpt-4",
    )
    agent = Agent(id="planner", config=config)
    runtime = AgentRuntime(agent=agent, llm_provider=MockLLMProvider())
    
    prompt = runtime._build_prompt("Test task", {})
    assert "step by step" in prompt.lower()
    
    # Test learning agent
    config.agent_type = AgentType.LEARNING
    agent = Agent(id="learner", config=config)
    runtime = AgentRuntime(agent=agent, llm_provider=MockLLMProvider())
    
    prompt = runtime._build_prompt("Test task", {})
    assert "past experiences" in prompt.lower()


# ==================== Token Management Tests ====================

@pytest.mark.asyncio
async def test_context_window_management(runtime):
    """Test token limit handling."""
    # Create very long context that exceeds limits
    long_context = "x" * 100000  # Very long string
    
    result = await runtime.execute("Test task", context={"data": long_context})
    
    # Should complete without error (context truncated)
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_context_truncation(runtime):
    """Test truncation when over limit."""
    # Set up memory with lots of context
    mock_memory = MockMemory()
    mock_memory.recent_memories = [
        Mock(content={"task": f"Task {i}", "response": "x" * 1000})
        for i in range(100)
    ]
    runtime.set_memory(mock_memory)
    
    result = await runtime.execute("Test task")
    
    # Should complete (memory context truncated)
    assert result["status"] == "completed"


# ==================== Batch Execution Tests ====================

@pytest.mark.asyncio
async def test_batch_execute(runtime):
    """Test parallel task execution."""
    tasks = ["Task 1", "Task 2", "Task 3"]
    
    results = await runtime.batch_execute(tasks)
    
    assert len(results) == 3
    for result in results:
        assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_batch_execute_with_errors(agent):
    """Test error handling in batch execution."""
    # Create provider that fails on second call
    mock_provider = MockLLMProvider()
    original_generate = mock_provider.generate
    
    async def failing_generate(*args, **kwargs):
        if mock_provider.call_count == 2:
            raise RuntimeError("Intentional failure")
        return await original_generate(*args, **kwargs)
    
    mock_provider.generate = failing_generate
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    tasks = ["Task 1", "Task 2", "Task 3"]
    results = await runtime.batch_execute(tasks)
    
    assert len(results) == 3
    # Some should succeed, one should have error
    errors = [r for r in results if "error" in r]
    assert len(errors) > 0


# ==================== Tool Integration Tests ====================

@pytest.mark.asyncio
async def test_set_tools(runtime):
    """Test setting tools."""
    mock_tool = Mock()
    tools = {"tool1": mock_tool, "tool2": mock_tool}
    
    runtime.set_tools(tools)
    
    assert runtime._tools == tools


@pytest.mark.asyncio
async def test_set_memory(runtime):
    """Test setting memory system."""
    mock_memory = MockMemory()
    
    runtime.set_memory(mock_memory)
    
    assert runtime._memory == mock_memory


# ==================== Error Handling Tests ====================

@pytest.mark.asyncio
async def test_execution_error_handling(agent):
    """Test error handling during execution."""
    # Create provider that always fails
    mock_provider = MockLLMProvider(fail_count=10)
    runtime = AgentRuntime(agent=agent, llm_provider=mock_provider)
    
    with pytest.raises(AgentExecutionError) as exc_info:
        await runtime.execute("Test task")
    
    assert "Agent execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_llm_provider_error():
    """Test error when no LLM provider available."""
    config = AgentConfig(role="Test", goal="Test", llm_model="gpt-4")
    agent = Agent(id="test", config=config)
    runtime = AgentRuntime(agent=agent, llm_provider=None)
    
    with pytest.raises(AgentExecutionError):
        await runtime.execute("Test task")


# ==================== Stats and Metrics Tests ====================

@pytest.mark.asyncio
async def test_token_usage_tracking(runtime):
    """Test token usage tracking."""
    initial_tokens = runtime.agent._total_tokens
    
    await runtime.execute("Test task")
    
    assert runtime.agent._total_tokens > initial_tokens
    assert runtime.agent._total_tokens == initial_tokens + 100  # Mock returns 100 tokens


@pytest.mark.asyncio
async def test_execution_count_tracking(runtime):
    """Test execution count tracking."""
    initial_count = runtime.agent._execution_count
    
    await runtime.execute("Test task")
    
    assert runtime.agent._execution_count == initial_count + 1
