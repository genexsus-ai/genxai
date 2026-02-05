"""Unit tests for tool registry."""

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory, ToolResult
from genxai.tools.registry import ToolRegistry


class DummyTool(Tool):
    def __init__(self) -> None:
        super().__init__(
            metadata=ToolMetadata(
                name="dummy",
                description="Dummy tool",
                category=ToolCategory.DATA,
                tags=["demo"],
            ),
            parameters=[
                ToolParameter(name="value", type="string", description="Value"),
            ],
        )

    async def _execute(self, **kwargs):
        return {"result": kwargs.get("value")}


def test_tool_registry_register_get_clear() -> None:
    ToolRegistry.clear()
    tool = DummyTool()
    ToolRegistry.register(tool)
    assert ToolRegistry.get("dummy") == tool
    ToolRegistry.clear()
    assert ToolRegistry.get("dummy") is None


def test_tool_registry_search_and_stats() -> None:
    ToolRegistry.clear()
    tool = DummyTool()
    ToolRegistry.register(tool)
    results = ToolRegistry.search("dummy")
    assert len(results) == 1
    stats = ToolRegistry.get_stats()
    assert stats["total_tools"] == 1
    assert "dummy" in stats["tool_names"]
    ToolRegistry.clear()


def test_tool_registry_export_schema_bundle() -> None:
    ToolRegistry.clear()
    tool = DummyTool()
    ToolRegistry.register(tool)
    bundle = ToolRegistry.export_schema_bundle()
    assert bundle["tool_count"] == 1
    assert bundle["schema_version"] == ToolRegistry.SCHEMA_VERSION
    ToolRegistry.clear()
