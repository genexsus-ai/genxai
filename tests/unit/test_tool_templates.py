"""Unit tests for tool templates."""

import asyncio
import json

import pytest

from genxai.tools.base import ToolCategory
from genxai.tools.templates import (
    create_tool_from_template,
    get_available_templates,
    TextProcessorTool,
    DataTransformerTool,
)


def test_get_available_templates() -> None:
    templates = get_available_templates()
    template_ids = {template["id"] for template in templates}
    assert "api_call" in template_ids
    assert "text_processor" in template_ids
    assert "data_transformer" in template_ids
    assert "file_processor" in template_ids


def test_create_tool_from_template() -> None:
    tool = create_tool_from_template(
        name="my_text",
        description="Text tool",
        category=ToolCategory.DATA,
        tags=["demo"],
        template="text_processor",
        config={"operation": "uppercase"},
    )
    assert isinstance(tool, TextProcessorTool)
    assert tool.metadata.name == "my_text"


def test_create_tool_from_template_invalid() -> None:
    with pytest.raises(ValueError):
        create_tool_from_template(
            name="bad",
            description="Bad",
            category=ToolCategory.DATA,
            tags=[],
            template="unknown",
            config={},
        )


def test_text_processor_tool() -> None:
    tool = TextProcessorTool(
        name="text",
        description="Text",
        category=ToolCategory.DATA,
        tags=[],
        config={"operation": "lowercase"},
    )

    async def run() -> None:
        result = await tool._execute("HELLO")
        assert result["result"] == "hello"

    asyncio.run(run())


def test_data_transformer_tool_json_to_csv() -> None:
    tool = DataTransformerTool(
        name="transform",
        description="Transform",
        category=ToolCategory.DATA,
        tags=[],
        config={"from_format": "json", "to_format": "csv"},
    )

    payload = json.dumps([
        {"name": "A", "value": 1},
        {"name": "B", "value": 2},
    ])

    async def run() -> None:
        result = await tool._execute(payload)
        assert "name" in result["result"]
        assert "value" in result["result"]

    asyncio.run(run())
