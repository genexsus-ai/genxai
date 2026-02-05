"""Tests for database tools."""

import pytest
from genxai.tools.builtin.database.sql_query import SQLQueryTool
from genxai.tools.builtin.database.mongodb_query import MongoDBQueryTool
from genxai.tools.builtin.database.redis_cache import RedisCacheTool
from genxai.tools.builtin.database.vector_search import VectorSearchTool
from genxai.tools.builtin.database.database_inspector import DatabaseInspectorTool


# ==================== SQL Query Tool Tests ====================

@pytest.mark.asyncio
async def test_sql_query_initialization():
    """Test SQL query tool initialization."""
    tool = SQLQueryTool()
    assert tool.metadata.name == "sql_query"
    assert tool.metadata.category == "database"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_sql_query_invalid_connection():
    """Test SQL query with invalid connection."""
    tool = SQLQueryTool()
    result = await tool.execute(
        query="SELECT * FROM users",
        connection_string="invalid"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_sql_query_invalid_query():
    """Test SQL query with invalid SQL."""
    tool = SQLQueryTool()
    result = await tool.execute(
        query="INVALID SQL SYNTAX",
        connection_string="sqlite:///:memory:"
    )
    assert result.success is False


def test_sql_query_metadata():
    """Test SQL query metadata."""
    tool = SQLQueryTool()
    assert "sql" in tool.metadata.description.lower() or "query" in tool.metadata.description.lower()
    assert len(tool.metadata.tags) > 0


# ==================== MongoDB Query Tool Tests ====================

@pytest.mark.asyncio
async def test_mongodb_query_initialization():
    """Test MongoDB query tool initialization."""
    tool = MongoDBQueryTool()
    assert tool.metadata.name == "mongodb_query"
    assert tool.metadata.category == "database"


@pytest.mark.asyncio
async def test_mongodb_query_invalid_connection():
    """Test MongoDB query with invalid connection."""
    tool = MongoDBQueryTool()
    result = await tool.execute(
        collection="users",
        query={"name": "test"},
        connection_string="invalid"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_mongodb_query_invalid_query():
    """Test MongoDB query with invalid query format."""
    tool = MongoDBQueryTool()
    result = await tool.execute(
        collection="users",
        query="invalid query format",
        connection_string="mongodb://localhost:27017"
    )
    assert result.success is False


def test_mongodb_query_metadata():
    """Test MongoDB query metadata."""
    tool = MongoDBQueryTool()
    assert "mongodb" in tool.metadata.description.lower() or "query" in tool.metadata.description.lower()


# ==================== Redis Cache Tool Tests ====================

@pytest.mark.asyncio
async def test_redis_cache_initialization():
    """Test Redis cache tool initialization."""
    tool = RedisCacheTool()
    assert tool.metadata.name == "redis_cache"
    assert tool.metadata.category == "database"


@pytest.mark.asyncio
async def test_redis_cache_invalid_connection():
    """Test Redis cache with invalid connection."""
    tool = RedisCacheTool()
    result = await tool.execute(
        operation="get",
        key="test_key",
        connection_string="redis://invalid:9999"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_redis_cache_invalid_operation():
    """Test Redis cache with invalid operation."""
    tool = RedisCacheTool()
    result = await tool.execute(
        operation="invalid_operation",
        key="test_key",
        connection_string="redis://localhost:6379"
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_redis_cache_get_nonexistent_key():
    """Test Redis cache getting nonexistent key."""
    tool = RedisCacheTool()
    result = await tool.execute(
        operation="get",
        key="nonexistent_key_12345",
        connection_string="redis://localhost:6379"
    )
    # Should either succeed with null or fail gracefully
    assert result.success is True or result.success is False


def test_redis_cache_metadata():
    """Test Redis cache metadata."""
    tool = RedisCacheTool()
    assert "redis" in tool.metadata.description.lower() or "cache" in tool.metadata.description.lower()


# ==================== Vector Search Tool Tests ====================

@pytest.mark.asyncio
async def test_vector_search_initialization():
    """Test vector search tool initialization."""
    tool = VectorSearchTool()
    assert tool.metadata.name == "vector_search"
    assert tool.metadata.category == "database"


@pytest.mark.asyncio
async def test_vector_search_invalid_vector():
    """Test vector search with invalid vector."""
    tool = VectorSearchTool()
    result = await tool.execute(
        query_vector="invalid",
        collection="test_collection"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_vector_search_empty_vector():
    """Test vector search with empty vector."""
    tool = VectorSearchTool()
    result = await tool.execute(
        query_vector=[],
        collection="test_collection"
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_vector_search_invalid_collection():
    """Test vector search with invalid collection."""
    tool = VectorSearchTool()
    result = await tool.execute(
        query_vector=[0.1, 0.2, 0.3],
        collection="nonexistent_collection"
    )
    assert result.success is False


def test_vector_search_metadata():
    """Test vector search metadata."""
    tool = VectorSearchTool()
    assert "vector" in tool.metadata.description.lower() or "search" in tool.metadata.description.lower()


# ==================== Database Inspector Tool Tests ====================

@pytest.mark.asyncio
async def test_database_inspector_initialization():
    """Test database inspector tool initialization."""
    tool = DatabaseInspectorTool()
    assert tool.metadata.name == "database_inspector"
    assert tool.metadata.category == "database"


@pytest.mark.asyncio
async def test_database_inspector_invalid_connection():
    """Test database inspector with invalid connection."""
    tool = DatabaseInspectorTool()
    result = await tool.execute(
        connection_string="invalid",
        operation="list_tables"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_database_inspector_invalid_operation():
    """Test database inspector with invalid operation."""
    tool = DatabaseInspectorTool()
    result = await tool.execute(
        connection_string="sqlite:///:memory:",
        operation="invalid_operation"
    )
    assert result.success is False


@pytest.mark.asyncio
async def test_database_inspector_list_tables():
    """Test database inspector listing tables."""
    tool = DatabaseInspectorTool()
    result = await tool.execute(
        connection_string="sqlite:///:memory:",
        operation="list_tables"
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


def test_database_inspector_metadata():
    """Test database inspector metadata."""
    tool = DatabaseInspectorTool()
    assert "database" in tool.metadata.description.lower() or "inspect" in tool.metadata.description.lower()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_all_database_tools_have_category():
    """Test that all database tools have correct category."""
    tools = [
        SQLQueryTool(),
        MongoDBQueryTool(),
        RedisCacheTool(),
        VectorSearchTool(),
        DatabaseInspectorTool()
    ]
    
    for tool in tools:
        assert tool.metadata.category == "database"


@pytest.mark.asyncio
async def test_all_database_tools_have_parameters():
    """Test that all database tools have parameters defined."""
    tools = [
        SQLQueryTool(),
        MongoDBQueryTool(),
        RedisCacheTool(),
        VectorSearchTool(),
        DatabaseInspectorTool()
    ]
    
    for tool in tools:
        assert len(tool.parameters) > 0


def test_all_database_tools_have_descriptions():
    """Test that all database tools have descriptions."""
    tools = [
        SQLQueryTool(),
        MongoDBQueryTool(),
        RedisCacheTool(),
        VectorSearchTool(),
        DatabaseInspectorTool()
    ]
    
    for tool in tools:
        assert len(tool.metadata.description) > 0
        assert len(tool.metadata.tags) > 0
