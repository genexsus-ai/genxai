"""Unit tests for the GenXAI MCP server."""

import json
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("mcp")

from genxai.tools.mcp_server import GenXAIMCPServer  # noqa: E402


class FakeServer:
    """Stands in for mcp.server.Server, capturing registered handlers."""

    def __init__(self, name):
        self.name = name
        self.handlers = {}

    def list_tools(self):
        def decorator(fn):
            self.handlers["list_tools"] = fn
            return fn

        return decorator

    def call_tool(self):
        def decorator(fn):
            self.handlers["call_tool"] = fn
            return fn

        return decorator


def _fake_tool(name="calculator", description="Does math"):
    tool = MagicMock()
    tool.metadata.name = name
    tool.metadata.description = description
    tool.get_schema.return_value = {
        "parameters": {
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        }
    }
    return tool


@pytest.fixture
def server():
    with patch("genxai.tools.mcp_server.Server", FakeServer):
        yield GenXAIMCPServer(name="test-server")


def test_server_registers_handlers(server):
    assert set(server.server.handlers) == {"list_tools", "call_tool"}
    assert server.server.name == "test-server"


def test_convert_to_mcp_tool(server):
    tool = _fake_tool()
    mcp_tool = server._convert_to_mcp_tool(tool)

    assert mcp_tool.name == "calculator"
    assert mcp_tool.description == "Does math"
    assert mcp_tool.inputSchema["type"] == "object"
    assert "expression" in mcp_tool.inputSchema["properties"]
    assert mcp_tool.inputSchema["required"] == ["expression"]


def test_format_tool_result_dict_and_scalar(server):
    assert json.loads(server._format_tool_result({"a": 1})) == {"a": 1}
    assert json.loads(server._format_tool_result([1, 2])) == [1, 2]
    assert server._format_tool_result(42) == "42"
    assert server._format_tool_result("text") == "text"


@pytest.mark.asyncio
async def test_list_tools_handler(server):
    tool = _fake_tool()
    with patch("genxai.tools.mcp_server.ToolRegistry.list_all", return_value=[tool]):
        tools = await server.server.handlers["list_tools"]()

    assert len(tools) == 1
    assert tools[0].name == "calculator"


@pytest.mark.asyncio
async def test_call_tool_unknown_tool_returns_error(server):
    with patch("genxai.tools.mcp_server.ToolRegistry.get", return_value=None):
        result = await server.server.handlers["call_tool"]("missing", {})

    assert result.isError is True
    assert "not found" in result.content[0].text


@pytest.mark.asyncio
async def test_call_tool_success(server):
    tool = _fake_tool()

    async def execute(**kwargs):
        outcome = MagicMock()
        outcome.success = True
        outcome.data = {"answer": 4}
        return outcome

    tool.execute = execute
    with patch("genxai.tools.mcp_server.ToolRegistry.get", return_value=tool):
        result = await server.server.handlers["call_tool"]("calculator", {"expression": "2+2"})

    assert result.isError is False
    assert json.loads(result.content[0].text) == {"answer": 4}


@pytest.mark.asyncio
async def test_call_tool_reports_tool_failure(server):
    tool = _fake_tool()

    async def execute(**kwargs):
        outcome = MagicMock()
        outcome.success = False
        outcome.error = "division by zero"
        return outcome

    tool.execute = execute
    with patch("genxai.tools.mcp_server.ToolRegistry.get", return_value=tool):
        result = await server.server.handlers["call_tool"]("calculator", {"expression": "1/0"})

    assert result.isError is True
    assert "division by zero" in result.content[0].text


@pytest.mark.asyncio
async def test_call_tool_handles_exception(server):
    tool = _fake_tool()

    async def execute(**kwargs):
        raise RuntimeError("kaboom")

    tool.execute = execute
    with patch("genxai.tools.mcp_server.ToolRegistry.get", return_value=tool):
        result = await server.server.handlers["call_tool"]("calculator", {})

    assert result.isError is True
    assert "kaboom" in result.content[0].text
