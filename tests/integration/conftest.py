"""Integration test fixtures and configuration."""

import pytest
import os
import sys
import asyncio
import importlib.util
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

from genxai.llm.factory import LLMProviderFactory
from genxai.core.memory.manager import MemorySystem
from genxai.tools.registry import ToolRegistry
from genxai.core.agent.base import Agent, AgentConfig, AgentType
from genxai.core.agent.runtime import AgentRuntime

TESTS_ROOT = Path(__file__).resolve().parents[1]
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from utils.mock_llm import MockLLMProvider


# Load environment variables from .env if present
load_dotenv()

# ==================== LLM Provider Fixtures ====================

def _close_provider(provider: Any) -> None:
    """Close LLM providers using a dedicated event loop."""
    if not hasattr(provider, "aclose"):
        return
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(provider.aclose())
        except RuntimeError as exc:
            if "Event loop is closed" not in str(exc):
                raise
    finally:
        try:
            loop.run_until_complete(asyncio.sleep(0))
        except RuntimeError:
            pass
        loop.close()
        asyncio.set_event_loop(None)

@pytest.fixture(scope="session")
def openai_provider():
    """Create OpenAI provider for integration tests (fallback to mock)."""
    if not importlib.util.find_spec("openai"):
        provider = MockLLMProvider()
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            provider = MockLLMProvider()
        else:
            model = os.getenv("OPENAI_MODEL", "gpt-4")
            try:
                provider = LLMProviderFactory.create_provider(model=model, api_key=api_key)
            except Exception:
                provider = MockLLMProvider()

    yield provider
    _close_provider(provider)


@pytest.fixture(scope="session")
def anthropic_provider():
    """Create Anthropic provider for integration tests."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
    provider = LLMProviderFactory.create_provider("anthropic", api_key=api_key)
    yield provider
    _close_provider(provider)


@pytest.fixture(scope="session")
def google_provider():
    """Create Google provider for integration tests."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")
    provider = LLMProviderFactory.create_provider("google", api_key=api_key)
    yield provider
    _close_provider(provider)


@pytest.fixture(scope="session")
def cohere_provider():
    """Create Cohere provider for integration tests."""
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        pytest.skip("COHERE_API_KEY not set")
    provider = LLMProviderFactory.create_provider("cohere", api_key=api_key)
    yield provider
    _close_provider(provider)


@pytest.fixture(scope="session")
def default_llm_provider(openai_provider):
    """Default LLM provider for tests (OpenAI or mock fallback)."""
    return openai_provider


@pytest.fixture(scope="session")
def mock_llm_provider():
    """Mock LLM provider for tests."""
    return MockLLMProvider()


# ==================== Memory System Fixtures ====================

@pytest.fixture
def memory_system():
    """Create memory system with in-memory storage."""
    return MemorySystem(agent_id="test_agent")


@pytest.fixture
def memory_system_with_redis():
    """Create memory system with Redis storage."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        return MemorySystem(agent_id="test_agent", redis_client=client)
    except Exception:
        pytest.skip("Redis not available")


# ==================== Tool Registry Fixtures ====================

@pytest.fixture(scope="session")
def tool_registry():
    """Create tool registry with all built-in tools."""
    registry = ToolRegistry()
    registry.discover_tools()
    return registry


@pytest.fixture
def web_tools(tool_registry):
    """Get web tools from registry."""
    return {
        name: tool
        for name, tool in tool_registry.get_all_tools().items()
        if "web" in name.lower()
    }


@pytest.fixture
def data_tools(tool_registry):
    """Get data tools from registry."""
    return {
        name: tool
        for name, tool in tool_registry.get_all_tools().items()
        if "json" in name.lower() or "csv" in name.lower() or "xml" in name.lower()
    }


@pytest.fixture
def file_tools(tool_registry):
    """Get file tools from registry."""
    return {
        name: tool
        for name, tool in tool_registry.get_all_tools().items()
        if "file" in name.lower() or "pdf" in name.lower()
    }


# ==================== Agent Fixtures ====================

@pytest.fixture
def test_agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        role="Test Agent",
        goal="Execute test tasks",
        backstory="A test agent for integration testing",
        llm_model="gpt-4",
        llm_temperature=0.7,
        tools=[],
    )


@pytest.fixture
def test_agent(test_agent_config):
    """Create test agent."""
    return Agent(id="test_agent", config=test_agent_config)


@pytest.fixture
def agent_runtime(test_agent, default_llm_provider):
    """Create agent runtime with default provider."""
    return AgentRuntime(agent=test_agent, llm_provider=default_llm_provider)


@pytest.fixture
def agent_runtime_with_memory(test_agent, default_llm_provider, memory_system):
    """Create agent runtime with memory system."""
    runtime = AgentRuntime(agent=test_agent, llm_provider=default_llm_provider)
    runtime.set_memory(memory_system)
    return runtime


@pytest.fixture
def agent_runtime_with_tools(test_agent, default_llm_provider, tool_registry):
    """Create agent runtime with tools."""
    runtime = AgentRuntime(agent=test_agent, llm_provider=default_llm_provider)
    runtime.set_tools(tool_registry.get_all_tools())
    return runtime


# ==================== Database Fixtures ====================

@pytest.fixture
def redis_client():
    """Create Redis client for testing."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        yield client
        # Cleanup
        client.flushdb()
    except Exception:
        pytest.skip("Redis not available")


@pytest.fixture
def mongodb_client():
    """Create MongoDB client for testing."""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    try:
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.admin.command("ping")
        yield client
        # Cleanup
        client.drop_database("test_db")
    except Exception:
        pytest.skip("MongoDB not available")


@pytest.fixture
def sqlite_connection():
    """Create SQLite connection for testing."""
    import sqlite3
    import tempfile
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    conn = sqlite3.connect(temp_db.name)
    
    # Create test table
    conn.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value INTEGER
        )
    """)
    conn.execute("INSERT INTO test_table VALUES (1, 'test1', 100)")
    conn.execute("INSERT INTO test_table VALUES (2, 'test2', 200)")
    conn.commit()
    
    yield conn
    
    # Cleanup
    conn.close()
    os.unlink(temp_db.name)


# ==================== Vector Store Fixtures ====================

@pytest.fixture
def chromadb_client():
    """Create ChromaDB client for testing."""
    try:
        import chromadb
        client = chromadb.Client()
        yield client
        # Cleanup
        client.reset()
    except ImportError:
        pytest.skip("ChromaDB not installed")


@pytest.fixture
def pinecone_index():
    """Create Pinecone index for testing."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        pytest.skip("PINECONE_API_KEY not set")
    
    try:
        import pinecone
        pinecone.init(api_key=api_key)
        
        index_name = "test-index"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(index_name, dimension=1536)
        
        yield pinecone.Index(index_name)
        
        # Cleanup
        pinecone.delete_index(index_name)
    except ImportError:
        pytest.skip("Pinecone not installed")


# ==================== Communication Fixtures ====================

@pytest.fixture
def slack_webhook_url():
    """Get Slack webhook URL for testing."""
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        pytest.skip("SLACK_WEBHOOK_URL not set")
    return url


@pytest.fixture
def test_email_config():
    """Get email configuration for testing."""
    config = {
        "smtp_host": os.getenv("SMTP_HOST"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_password": os.getenv("SMTP_PASSWORD"),
        "from_email": os.getenv("FROM_EMAIL"),
    }
    
    if not all([config["smtp_host"], config["smtp_user"], config["smtp_password"]]):
        pytest.skip("Email configuration not set")
    
    return config


# ==================== Performance Fixtures ====================

@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""
    import time
    
    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
        
        def start(self, name: str):
            """Start timing an operation."""
            self.metrics[name] = {"start": time.time()}
        
        def end(self, name: str):
            """End timing an operation."""
            if name in self.metrics:
                self.metrics[name]["end"] = time.time()
                self.metrics[name]["duration"] = (
                    self.metrics[name]["end"] - self.metrics[name]["start"]
                )
        
        def get_duration(self, name: str) -> float:
            """Get duration of an operation."""
            return self.metrics.get(name, {}).get("duration", 0.0)
        
        def get_all_metrics(self) -> Dict[str, Any]:
            """Get all metrics."""
            return self.metrics
    
    return PerformanceTracker()


# ==================== Async Fixtures ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== Cleanup ====================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test."""
    import tempfile
    import shutil
    
    temp_dirs = []
    
    yield
    
    # Cleanup
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# ==================== Test Markers ====================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: mark test as requiring API keys"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "requires_mongodb: mark test as requiring MongoDB"
    )


def pytest_collection_modifyitems(config, items):
    """Dynamically skip integration tests based on environment/dependencies.

    This makes the integration suite runnable on machines that don't have all
    external dependencies installed (or all secrets configured).

    To run real LLM integration tests:
      - install provider deps: `pip install -e '.[llm]'`
      - export OPENAI_API_KEY
    """

    openai_installed = bool(importlib.util.find_spec("openai"))
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    for item in items:
        if item.get_closest_marker("requires_api_key"):
            if not (openai_installed and has_openai_key):
                reason_parts = []
                if not openai_installed:
                    reason_parts.append("openai package not installed")
                if not has_openai_key:
                    reason_parts.append("OPENAI_API_KEY not set")
                item.add_marker(pytest.mark.skip(reason="; ".join(reason_parts)))
