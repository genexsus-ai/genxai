"""Tests for YAML config import/export utilities."""

from __future__ import annotations

from pathlib import Path

from genxai.core.agent.base import Agent, AgentConfig
from genxai.core.agent.config_io import (
    export_agent_config_yaml,
    export_agents_yaml,
    import_agent_config_yaml,
    import_agents_yaml,
)


def test_agent_config_yaml_round_trip(tmp_path: Path) -> None:
    agent = Agent(
        id="agent-1",
        config=AgentConfig(
            role="planner",
            goal="Plan things",
            tools=["search"],
            allowed_domains=["example.com"],
        ),
    )

    path = tmp_path / "agent.yaml"
    export_agent_config_yaml(agent, path)
    loaded = import_agent_config_yaml(path)

    assert loaded.id == agent.id
    assert loaded.config.role == agent.config.role
    assert loaded.config.tools == agent.config.tools


def test_agents_yaml_round_trip(tmp_path: Path) -> None:
    agents = [
        Agent(id="a1", config=AgentConfig(role="writer", goal="Write")),
        Agent(id="a2", config=AgentConfig(role="reviewer", goal="Review")),
    ]

    path = tmp_path / "agents.yaml"
    export_agents_yaml(agents, path)
    loaded = import_agents_yaml(path)

    assert [agent.id for agent in loaded] == ["a1", "a2"]
    assert loaded[1].config.role == "reviewer"