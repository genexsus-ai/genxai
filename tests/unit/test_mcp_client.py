"""Tests for the MCP tool client against a real stdio fixture server."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from genxai.tools.mcp_client import MCPClientError, MCPToolClient  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mcp_fixture_server.py"


def _client() -> MCPToolClient:
    return MCPToolClient(command=sys.executable, args=[str(FIXTURE)])


def test_requires_exactly_one_transport():
    with pytest.raises(ValueError):
        MCPToolClient()
    with pytest.raises(ValueError):
        MCPToolClient(command="x", url="http://y")


@pytest.mark.asyncio
async def test_list_tools_from_stdio_server():
    tools = await _client().list_tools()
    names = {tool["name"] for tool in tools}
    assert {"echo", "add"} <= names
    add = next(tool for tool in tools if tool["name"] == "add")
    assert "a" in add["input_schema"].get("properties", {})


@pytest.mark.asyncio
async def test_call_tool_text_and_structured():
    client = _client()

    echoed = await client.call_tool("echo", {"message": "hello"})
    assert echoed["is_error"] is False
    assert echoed["text"] == "echo: hello"

    summed = await client.call_tool("add", {"a": 40, "b": 2})
    assert summed["structured"] == {"sum": 42.0} or summed["structured"] == {"sum": 42}


@pytest.mark.asyncio
async def test_unreachable_server_raises_clear_error():
    bad = MCPToolClient(command=sys.executable, args=["-c", "import sys; sys.exit(1)"])
    with pytest.raises(MCPClientError):
        await bad.list_tools()
