"""Workflow YAML loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from genxai.core.agent.base import Agent
from genxai.core.agent.registry import AgentRegistry
from genxai.core.agent.config_io import import_agents_yaml


def load_workflow_yaml(path: Path) -> Dict[str, Any]:
    """Load a workflow YAML file.

    Supports `agents_ref` to pull reusable agent definitions from another YAML file.
    Inline agents remain supported and will be merged with referenced agents.
    """
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict) or "workflow" not in payload:
        raise ValueError("Workflow YAML must contain a top-level 'workflow' mapping")

    workflow = payload["workflow"]
    if not isinstance(workflow, dict):
        raise ValueError("workflow must be a mapping")

    _merge_agents_ref(workflow, base_path=path.parent)
    _validate_workflow_schema(workflow)
    return workflow


def register_workflow_agents(workflow: Dict[str, Any]) -> List[Agent]:
    """Register agents defined in a workflow dict and return them.

    Accepts agent dictionaries with the `agents_ref` already resolved.
    """
    agents_payload = workflow.get("agents", [])
    if not agents_payload:
        return []

    workflow_memory = workflow.get("memory") if isinstance(workflow.get("memory"), dict) else {}

    agents: List[Agent] = []
    for agent_data in agents_payload:
        if not isinstance(agent_data, dict):
            raise ValueError("Invalid agent definition in workflow")
        merged_agent = _apply_workflow_memory_defaults(agent_data, workflow_memory)
        agent = _agent_from_workflow_dict(merged_agent)
        AgentRegistry.register(agent)
        agents.append(agent)
    return agents


def _apply_workflow_memory_defaults(
    agent_data: Dict[str, Any], workflow_memory: Dict[str, Any]
) -> Dict[str, Any]:
    if not workflow_memory:
        return agent_data

    defaults: Dict[str, Any] = {}
    if "enabled" in workflow_memory:
        defaults["enabled"] = workflow_memory.get("enabled")
    if "type" in workflow_memory:
        defaults["type"] = workflow_memory.get("type")

    if not defaults:
        return agent_data

    if isinstance(agent_data.get("memory"), dict):
        memory_block = dict(agent_data.get("memory") or {})
        memory_block.setdefault("enabled", defaults.get("enabled"))
        memory_block.setdefault("type", defaults.get("type"))
        agent_data = {**agent_data, "memory": memory_block}
        return agent_data

    if "enable_memory" in agent_data or "memory_type" in agent_data:
        return agent_data

    return {**agent_data, "memory": {k: v for k, v in defaults.items() if v is not None}}


def _merge_agents_ref(workflow: Dict[str, Any], base_path: Path) -> None:
    agents_ref = workflow.get("agents_ref")
    if not agents_ref:
        return

    agents_ref_path = (base_path / agents_ref).resolve()
    referenced = import_agents_yaml(agents_ref_path)
    referenced_dicts = [
        {"id": agent.id, **agent.config.model_dump(mode="json")}
        if isinstance(agent, Agent)
        else dict(agent)
        for agent in referenced
    ]

    inline_agents = workflow.get("agents", [])
    if inline_agents is None:
        inline_agents = []
    if not isinstance(inline_agents, list):
        raise ValueError("workflow.agents must be a list")

    # Merge with inline agents taking precedence by id.
    merged = {agent["id"]: agent for agent in referenced_dicts if isinstance(agent, dict)}
    for agent in inline_agents:
        if not isinstance(agent, dict) or "id" not in agent:
            raise ValueError("Invalid inline agent definition")
        merged[agent["id"]] = agent

    workflow["agents"] = list(merged.values())


def _validate_workflow_schema(workflow: Dict[str, Any]) -> None:
    if not workflow.get("name"):
        raise ValueError("workflow.name is required")

    if "memory" in workflow and not isinstance(workflow.get("memory"), dict):
        raise ValueError("workflow.memory must be a mapping when provided")

    graph = workflow.get("graph")
    if not isinstance(graph, dict):
        raise ValueError("workflow.graph must be a mapping")

    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("workflow.graph.nodes must be a non-empty list")

    edges = graph.get("edges")
    if not isinstance(edges, list):
        raise ValueError("workflow.graph.edges must be a list")

    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("workflow.graph.nodes entries must be mappings")
        if "id" not in node or "type" not in node:
            raise ValueError("Each node requires 'id' and 'type'")
        node_ids.add(node["id"])
        if node["type"] not in {"input", "start", "output", "end", "agent", "tool", "condition"}:
            raise ValueError(f"Unsupported node type: {node['type']}")

    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("workflow.graph.edges entries must be mappings")
        if "from" not in edge or "to" not in edge:
            raise ValueError("Each edge requires 'from' and 'to'")
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            raise ValueError("Edges must reference existing node ids")

    agent_ids = {agent.get("id") for agent in workflow.get("agents", []) if isinstance(agent, dict)}
    for node in nodes:
        if node.get("type") == "agent" and node.get("id") not in agent_ids:
            raise ValueError(f"Agent node '{node['id']}' has no matching agent definition")


def _agent_from_workflow_dict(data: Dict[str, Any]) -> Agent:
    config_payload = data.get("config") if isinstance(data.get("config"), dict) else {}
    merged = {
        **config_payload,
        **{k: v for k, v in data.items() if k not in {"config"}},
    }
    return Agent(
        id=data["id"],
        config=_agent_config_from_workflow_dict(merged),
    )


def _agent_config_from_workflow_dict(data: Dict[str, Any]):
    from genxai.core.agent.base import AgentConfig

    # Allow workflow agents to specify either `llm` (legacy) or `llm_model`.
    llm_model = data.get("llm_model") or data.get("llm") or "gpt-4"

    return AgentConfig(
        role=data.get("role", "Agent"),
        goal=data.get("goal", "Process tasks"),
        backstory=data.get("backstory", ""),
        llm_provider=data.get("llm_provider", "openai"),
        llm_model=llm_model,
        llm_temperature=data.get("llm_temperature", 0.7),
        tools=data.get("tools", []),
        enable_llm_ranking=data.get("enable_llm_ranking", False),
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
