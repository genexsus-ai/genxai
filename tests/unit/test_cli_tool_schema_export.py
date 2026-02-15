"""CLI tests for tool schema export command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from genxai.cli.commands.tool import tool
from genxai.tools.registry import ToolRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure ToolRegistry is clean for each test."""
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


def test_export_schema_stdout_json():
    runner = CliRunner()
    result = runner.invoke(tool, ["export-schema", "--stdout"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == ToolRegistry.SCHEMA_VERSION


def test_export_schema_yaml_file(tmp_path: Path):
    runner = CliRunner()
    output_path = tmp_path / "schemas.yaml"

    result = runner.invoke(
        tool,
        [
            "export-schema",
            "--format",
            "yaml",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()

    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")

    content = yaml.safe_load(output_path.read_text())
    assert content["schema_version"] == ToolRegistry.SCHEMA_VERSION


def test_export_schema_invalid_category():
    runner = CliRunner()

    result = runner.invoke(tool, ["export-schema", "--category", "invalid"])

    assert result.exit_code != 0
    assert "Invalid category" in result.output


def test_export_schema_yaml_file_without_pyyaml(monkeypatch, tmp_path: Path):
    runner = CliRunner()

    import builtins

    real_import = builtins.__import__

    def _missing_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _missing_yaml)

    output_path = tmp_path / "schemas.yaml"
    result = runner.invoke(
        tool,
        ["export-schema", "--format", "yaml", "--output", str(output_path)],
    )

    assert result.exit_code != 0
    assert "PyYAML is required" in result.output


def test_export_schema_yaml_stdout_without_pyyaml(monkeypatch):
    runner = CliRunner()

    import builtins

    real_import = builtins.__import__

    def _missing_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _missing_yaml)

    result = runner.invoke(tool, ["export-schema", "--stdout", "--format", "yaml"])

    assert result.exit_code != 0
    assert "PyYAML is required" in result.output