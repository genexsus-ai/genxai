"""MCP (Model Context Protocol) server for GenXAI tools.

This module provides an MCP server that exposes GenXAI tools to external
applications like Claude Desktop, IDEs, and other AI systems.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool as MCPTool, TextContent, CallToolResult

from genxai.tools.registry import ToolRegistry
from genxai.tools.base import Tool, ToolCategory

logger = logging.getLogger(__name__)


class GenXAIMCPServer:
    """MCP server for GenXAI tools."""

    def __init__(self, name: str = "genxai-tools"):
        """Initialize MCP server.

        Args:
            name: Server name
        """
        self.server = Server(name)
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[MCPTool]:
            """List all available GenXAI tools."""
            tools = ToolRegistry.list_all()
            mcp_tools = []

            for tool in tools:
                mcp_tool = self._convert_to_mcp_tool(tool)
                mcp_tools.append(mcp_tool)

            logger.info(f"Listed {len(mcp_tools)} tools via MCP")
            return mcp_tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute a GenXAI tool.

            Args:
                name: Tool name
                arguments: Tool arguments

            Returns:
                Tool execution result
            """
            logger.info(f"MCP tool call: {name} with args: {arguments}")

            # Get tool from registry
            tool = ToolRegistry.get(name)
            if not tool:
                error_msg = f"Tool '{name}' not found"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )

            try:
                # Execute tool
                result = await tool.execute(**arguments)

                if result.success:
                    # Format successful result
                    content = self._format_tool_result(result.data)
                    return CallToolResult(
                        content=[TextContent(type="text", text=content)],
                        isError=False,
                    )
                else:
                    # Format error result
                    error_msg = result.error or "Tool execution failed"
                    logger.error(f"Tool {name} failed: {error_msg}")
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True,
                    )

            except Exception as e:
                error_msg = f"Tool execution error: {str(e)}"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True,
                )

    def _convert_to_mcp_tool(self, tool: Tool) -> MCPTool:
        """Convert GenXAI tool to MCP tool format.

        Args:
            tool: GenXAI tool

        Returns:
            MCP tool definition
        """
        schema = tool.get_schema()

        return MCPTool(
            name=tool.metadata.name,
            description=tool.metadata.description,
            inputSchema={
                "type": "object",
                "properties": schema["parameters"]["properties"],
                "required": schema["parameters"].get("required", []),
            },
        )

    def _format_tool_result(self, data: Any) -> str:
        """Format tool result for MCP response.

        Args:
            data: Tool result data

        Returns:
            Formatted string
        """
        import json

        if isinstance(data, (dict, list)):
            return json.dumps(data, indent=2)
        return str(data)

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting GenXAI MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


async def main():
    """Main entry point for MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Register built-in tools
    from genxai.tools.builtin.computation.calculator import CalculatorTool
    from genxai.tools.builtin.file.file_reader import FileReaderTool

    ToolRegistry.register(CalculatorTool())
    ToolRegistry.register(FileReaderTool())

    # Create and run server
    server = GenXAIMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
