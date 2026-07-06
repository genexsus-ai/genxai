"""MCP (Model Context Protocol) client for calling tools on external servers.

This is the client-side counterpart to :mod:`genxai.tools.mcp_server`: it
connects to an MCP server (local stdio process or remote HTTP endpoint),
lists its tools, and invokes them. Connections are opened per call, which
keeps the client stateless and safe to use from workflows and agents.

Requires the optional ``mcp`` package (``pip install mcp``).
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)


class MCPClientError(RuntimeError):
    """Raised when an MCP server cannot be reached or a call fails."""


class MCPToolClient:
    """Calls tools on a single MCP server.

    Exactly one transport must be configured:

    - stdio: ``command`` (+ optional ``args``/``env``) spawns a local server
    - HTTP:  ``url`` (+ optional ``headers``); endpoints ending in ``/sse``
      use the SSE transport, everything else uses streamable HTTP
    """

    def __init__(
        self,
        *,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        url: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        if bool(command) == bool(url):
            raise ValueError("Configure exactly one of 'command' (stdio) or 'url' (HTTP)")
        self.command = command
        self.args = args or []
        self.env = env or None
        self.url = url
        self.headers = headers or None
        self.timeout = timeout

    @asynccontextmanager
    async def _session(self):
        try:
            from mcp import ClientSession, StdioServerParameters
        except ImportError as exc:
            raise MCPClientError(
                "The 'mcp' package is required for MCP nodes. Install with: pip install mcp"
            ) from exc

        if self.command:
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(command=self.command, args=self.args, env=self.env)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        elif self.url and self.url.rstrip("/").endswith("/sse"):
            from mcp.client.sse import sse_client

            async with sse_client(self.url, headers=self.headers) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        else:
            from mcp.client.streamable_http import streamablehttp_client

            async with streamablehttp_client(self.url, headers=self.headers) as (
                read,
                write,
                _,
            ):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    async def list_tools(self) -> list[dict[str, Any]]:
        """Return the server's tools as plain dicts (name, description, input_schema)."""
        try:
            async with self._session() as session:
                result = await session.list_tools()
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(f"Could not list tools from MCP server: {exc}") from exc
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema or {},
            }
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke a tool and normalize the result to a plain dict.

        Returns ``{"is_error", "text", "content", "structured"}`` where
        ``text`` joins all text blocks, ``content`` lists each block, and
        ``structured`` carries structured output (or parsed JSON text) when
        available.
        """
        try:
            async with self._session() as session:
                result = await session.call_tool(name, arguments or {})
        except MCPClientError:
            raise
        except Exception as exc:
            raise MCPClientError(f"MCP tool call '{name}' failed: {exc}") from exc

        blocks: list[dict[str, Any]] = []
        texts: list[str] = []
        for item in result.content or []:
            item_type = getattr(item, "type", None)
            if item_type == "text":
                texts.append(item.text)
                blocks.append({"type": "text", "text": item.text})
            else:
                blocks.append({"type": item_type or "unknown", "repr": str(item)})

        text = "\n".join(texts)
        structured = getattr(result, "structuredContent", None)
        # FastMCP wraps plain (non-model) return values as {"result": <str>};
        # unwrap so callers get the actual payload.
        if (
            isinstance(structured, dict)
            and set(structured) == {"result"}
            and isinstance(structured["result"], str)
        ):
            try:
                structured = json.loads(structured["result"])
            except (json.JSONDecodeError, ValueError):
                structured = structured["result"]
        if structured is None and len(texts) == 1:
            try:
                structured = json.loads(texts[0])
            except (json.JSONDecodeError, ValueError):
                structured = None

        return {
            "is_error": bool(getattr(result, "isError", False)),
            "text": text,
            "content": blocks,
            "structured": structured,
        }
