"""YAML import/export utilities for agent configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List
import yaml

from genxai.core.agent.base import Agent, AgentConfig


def agent_config_to_dict(config: AgentConfig) -> Dict[str, Any]:
    """Serialize AgentConfig to a dictionary."""
    return config.model_dump(mode="json")


def agent_config_from_dict(data: Dict[str, Any]) -> AgentConfig:
    """Load AgentConfig from a dictionary."""
    return AgentConfig(**data)


def agent_to_dict(agent: Agent) -> Dict[str, Any]:
    """Serialize Agent to a dictionary."""
    return {"id": agent.id, "config": agent_config_to_dict(agent.config)}


def agent_from_dict(data: Dict[str, Any]) -> Agent:
    """Load Agent from a dictionary."""
    if "config" in data and isinstance(data.get("config"), dict):
        config = agent_config_from_dict(data["config"])
        return Agent(id=data["id"], config=config)

    # Support flat agent definitions (no config wrapper).
    llm_model = data.get("llm_model") or data.get("llm") or "gpt-4"
    config = AgentConfig(
        role=data.get("role", "Agent"),
        goal=data.get("goal", "Process tasks"),
        backstory=data.get("backstory", ""),
        llm_provider=data.get("llm_provider", "openai"),
        llm_model=llm_model,
        llm_temperature=data.get("llm_temperature", 0.7),
        tools=data.get("tools", []),
        enable_memory=data.get("memory", {}).get("enabled", True)
        if isinstance(data.get("memory"), dict)
        else data.get("enable_memory", True),
        memory_type=data.get("memory", {}).get("type", "short_term")
        if isinstance(data.get("memory"), dict)
        else data.get("memory_type", "short_term"),
        agent_type=data.get("behavior", {}).get("agent_type", "reactive")
        if isinstance(data.get("behavior"), dict)
        else data.get("agent_type", "reactive"),
        max_iterations=data.get("behavior", {}).get("max_iterations", 10)
        if isinstance(data.get("behavior"), dict)
        else data.get("max_iterations", 10),
        verbose=data.get("behavior", {}).get("verbose", False)
        if isinstance(data.get("behavior"), dict)
        else data.get("verbose", False),
        metadata=data.get("metadata", {}),
    )
    return Agent(id=data["id"], config=config)


def export_agent_config_yaml(agent: Agent, path: Path) -> None:
    """Export an agent configuration to a YAML file."""
    payload = agent_to_dict(agent)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def import_agent_config_yaml(path: Path) -> Agent:
    """Import an agent configuration from a YAML file."""
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Invalid YAML format for agent config")
    return agent_from_dict(data)


def export_agents_yaml(agents: Iterable[Agent], path: Path) -> None:
    """Export a list of agents to YAML."""
    payload = {"agents": [agent_to_dict(agent) for agent in agents]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def import_agents_yaml(path: Path) -> List[Agent]:
    """Import a list of agents from YAML."""
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "agents" not in data:
        raise ValueError("Invalid YAML format for agents list")
    if not isinstance(data["agents"], list):
        raise ValueError("Invalid YAML format for agents list")
    return [agent_from_dict(item) for item in data["agents"]]