"""Sync workflow agent nodes into the agents catalog."""

from __future__ import annotations

import hashlib
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    # When running from repo root
    from studio.backend.services.db import fetch_all, execute, json_dumps, json_loads
except ModuleNotFoundError:
    # When running from within studio/backend
    from services.db import fetch_all, execute, json_dumps, json_loads


def normalize_tools(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def normalize_metadata(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {}


def sync_agents_from_workflows():
    workflows = fetch_all("SELECT id, nodes FROM workflows")
    existing_agents = fetch_all("SELECT id, role, goal FROM agents")
    existing_keys = {f"{agent['role'].strip()}::{agent['goal'].strip()}" for agent in existing_agents}

    created_ids = []
    skipped = 0

    for workflow in workflows:
        workflow_id = workflow["id"]
        nodes = json_loads(workflow.get("nodes"), [])
        for node in nodes:
            if node.get("type") != "agent":
                continue
            config = node.get("config", {})
            role = (config.get("role") or node.get("label") or "").strip()
            goal = (config.get("goal") or "").strip()
            if not role or not goal:
                skipped += 1
                continue
            key = f"{role}::{goal}"
            if key in existing_keys:
                skipped += 1
                continue

            backstory = (config.get("backstory") or "").strip()
            llm_model = (config.get("llm_model") or "gpt-4").strip()
            tools = normalize_tools(config.get("tools"))
            metadata = normalize_metadata(config.get("metadata"))
            metadata = {
                **metadata,
                "source": "workflow_sync",
                "workflow_id": workflow_id,
                "node_id": node.get("id"),
            }

            identity = f"{role}|{goal}|{workflow_id}|{node.get('id')}"
            identity_hash = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:8]
            agent_id = f"agent_workflow_{identity_hash}"

            execute(
                """
                INSERT INTO agents (id, role, goal, backstory, llm_model, tools, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    role,
                    goal,
                    backstory,
                    llm_model,
                    json_dumps(tools),
                    json_dumps(metadata),
                ),
            )
            created_ids.append(agent_id)
            existing_keys.add(key)

    return {"synced": len(created_ids), "skipped": skipped, "created_ids": created_ids}


if __name__ == "__main__":
    result = sync_agents_from_workflows()
    print(
        "Workflow agent sync complete:"
        f" {result['synced']} created,"
        f" {result['skipped']} skipped"
    )
    if result["created_ids"]:
        print("Created IDs:")
        for agent_id in result["created_ids"]:
            print(f" - {agent_id}")