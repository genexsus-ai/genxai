"""Minimal stdio MCP server used by tests (echo + add tools)."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("genxai-test-fixture")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back."""
    return f"echo: {message}"


@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers; returns JSON with the sum."""
    import json

    return json.dumps({"sum": a + b})


if __name__ == "__main__":
    mcp.run(transport="stdio")
