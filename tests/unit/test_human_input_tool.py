"""Tests for human_input tool registration and metadata."""

from genxai.tools.registry import ToolRegistry


def test_human_input_tool_registered() -> None:
    ToolRegistry.clear()
    from genxai.tools.builtin import HumanInputTool  # noqa: F401 - triggers registration

    tool = ToolRegistry.get("human_input")
    if tool is None:
        HumanInputTool()
        tool = ToolRegistry.get("human_input")

    assert tool is not None
    assert tool.metadata.name == "human_input"
    assert "prompt" in [param.name for param in tool.parameters]