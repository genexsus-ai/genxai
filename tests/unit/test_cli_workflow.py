"""Tests for workflow CLI commands."""

import json
from pathlib import Path

from click.testing import CliRunner

from genxai.cli.commands.workflow import workflow
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.workflow_io import load_workflow_yaml, register_workflow_agents


def test_workflow_run_with_agents_ref(tmp_path: Path) -> None:
    agents_yaml = tmp_path / "agents.yaml"
    agents_yaml.write_text(
        """
agents:
  - id: "agent_one"
    role: "Agent One"
    goal: "Do something"
    llm_model: "gpt-4"
""".strip()
    )

    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Test Workflow"
  agents_ref: "agents.yaml"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_one"
        type: "agent"
      - id: "end"
        type: "output"
    edges:
      - from: "start"
        to: "agent_one"
      - from: "agent_one"
        to: "end"
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] in {"success", "error"}


def test_workflow_run_missing_agents_ref(tmp_path: Path) -> None:
    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Missing Agents"
  agents_ref: "missing.yaml"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_one"
        type: "agent"
      - id: "end"
        type: "output"
    edges:
      - from: "start"
        to: "agent_one"
      - from: "agent_one"
        to: "end"
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code != 0


def test_workflow_run_invalid_edges(tmp_path: Path) -> None:
    agents_yaml = tmp_path / "agents.yaml"
    agents_yaml.write_text(
        """
agents:
  - id: "agent_one"
    role: "Agent One"
    goal: "Do something"
    llm_model: "gpt-4"
""".strip()
    )

    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Invalid Edges"
  agents_ref: "agents.yaml"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_one"
        type: "agent"
      - id: "end"
        type: "output"
    edges: "not-a-list"
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code != 0


def test_workflow_run_missing_name(tmp_path: Path) -> None:
    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  graph:
    nodes:
      - id: "start"
        type: "input"
    edges: []
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code != 0


def test_workflow_run_unsupported_node_type(tmp_path: Path) -> None:
    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Unsupported Node"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "weird"
        type: "mystery"
    edges: []
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code != 0


def test_workflow_run_agent_without_definition(tmp_path: Path) -> None:
    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Missing Agent"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_one"
        type: "agent"
      - id: "end"
        type: "output"
    edges:
      - from: "start"
        to: "agent_one"
      - from: "agent_one"
        to: "end"
""".strip()
    )

    runner = CliRunner()
    result = runner.invoke(
        workflow,
        ["run", str(workflow_yaml), "--input", json.dumps({"task": "hello"})],
    )

    assert result.exit_code != 0


def test_workflow_memory_defaults_apply(tmp_path: Path) -> None:
    workflow_yaml = tmp_path / "workflow.yaml"
    workflow_yaml.write_text(
        """
workflow:
  name: "Memory Defaults"
  memory:
    enabled: false
    type: "long_term"
  agents:
    - id: "agent_default"
      role: "Default Agent"
    - id: "agent_override"
      role: "Override Agent"
      memory:
        enabled: true
        type: "short_term"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_default"
        type: "agent"
      - id: "agent_override"
        type: "agent"
      - id: "end"
        type: "output"
    edges:
      - from: "start"
        to: "agent_default"
      - from: "agent_default"
        to: "agent_override"
      - from: "agent_override"
        to: "end"
""".strip()
    )

    AgentRegistry.clear()
    workflow_dict = load_workflow_yaml(workflow_yaml)
    register_workflow_agents(workflow_dict)

    default_agent = AgentRegistry.get("agent_default")
    override_agent = AgentRegistry.get("agent_override")

    assert default_agent is not None
    assert override_agent is not None

    assert default_agent.config.enable_memory is False
    assert default_agent.config.memory_type == "long_term"

    assert override_agent.config.enable_memory is True
    assert override_agent.config.memory_type == "short_term"
