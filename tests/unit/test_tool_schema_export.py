"""Unit tests for tool schema export bundle."""

import json
from pathlib import Path

import pytest

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory
from genxai.tools.registry import ToolRegistry


class DummyTool(Tool):
    """Minimal tool for schema export testing."""

    def __init__(self, name: str, category: ToolCategory) -> None:
        metadata = ToolMetadata(
            name=name,
            description="Dummy tool",
            category=category,
        )
        parameters = [
            ToolParameter(
                name="input",
                type="string",
                description="Input text",
            )
        ]
        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs):
        return {"ok": True}


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure ToolRegistry is clean for each test."""
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


def test_export_schema_bundle_includes_version_and_tools():
    ToolRegistry.register(DummyTool("dummy", ToolCategory.WEB))

    bundle = ToolRegistry.export_schema_bundle()

    assert bundle["schema_version"] == ToolRegistry.SCHEMA_VERSION
    assert bundle["tool_count"] == 1
    assert bundle["tools"][0]["name"] == "dummy"


def test_export_schema_bundle_filters_by_category():
    ToolRegistry.register(DummyTool("web_tool", ToolCategory.WEB))
    ToolRegistry.register(DummyTool("file_tool", ToolCategory.FILE))

    bundle = ToolRegistry.export_schema_bundle(category=ToolCategory.WEB)

    assert bundle["tool_count"] == 1
    assert bundle["tools"][0]["name"] == "web_tool"


def test_export_schema_bundle_to_json_file(tmp_path: Path):
    ToolRegistry.register(DummyTool("dummy", ToolCategory.WEB))

    output_path = tmp_path / "schemas.json"
    exported_path = ToolRegistry.export_schema_bundle_to_file(str(output_path))

    assert Path(exported_path).exists()
    content = json.loads(Path(exported_path).read_text())
    assert content["tool_count"] == 1


def test_export_schema_bundle_to_yaml_file(tmp_path: Path):
    ToolRegistry.register(DummyTool("dummy", ToolCategory.WEB))

    output_path = tmp_path / "schemas.yaml"
    exported_path = ToolRegistry.export_schema_bundle_to_file(str(output_path))

    assert Path(exported_path).exists()

    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")

    content = yaml.safe_load(Path(exported_path).read_text())
    assert content["tool_count"] == 1