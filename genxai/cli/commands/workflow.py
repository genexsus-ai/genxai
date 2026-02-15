"""Workflow CLI commands (OSS)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import click

from genxai.core.graph import load_workflow_yaml, register_workflow_agents
from genxai.core.graph.executor import WorkflowExecutor


@click.group()
def workflow() -> None:
    """Manage and run workflows."""


@workflow.command("run")
@click.argument("workflow_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--input", "input_payload", required=True, help="JSON input payload")
def run_workflow(workflow_path: Path, input_payload: str) -> None:
    """Run a workflow from a YAML file."""

    import json

    try:
        workflow_dict = load_workflow_yaml(workflow_path)
    except (ValueError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    register_workflow_agents(workflow_dict)

    nodes = _build_nodes_from_workflow(workflow_dict)
    edges = _build_edges_from_workflow(workflow_dict)

    executor = WorkflowExecutor()
    input_data = json.loads(input_payload)
    shared_memory = workflow_dict.get("memory", {}).get("shared", False)

    result = _run_executor(executor, nodes, edges, input_data, shared_memory=shared_memory)
    click.echo(json.dumps(result, indent=2))


def _build_nodes_from_workflow(workflow_dict: Dict[str, Any]):
    nodes = workflow_dict.get("graph", {}).get("nodes", [])
    if not isinstance(nodes, list):
        raise click.ClickException("workflow.graph.nodes must be a list")
    return nodes


def _build_edges_from_workflow(workflow_dict: Dict[str, Any]):
    edges = workflow_dict.get("graph", {}).get("edges", [])
    if not isinstance(edges, list):
        raise click.ClickException("workflow.graph.edges must be a list")
    return [
        {
            "source": edge.get("from"),
            "target": edge.get("to"),
            "condition": edge.get("condition"),
        }
        for edge in edges
    ]


def _run_executor(
    executor: WorkflowExecutor,
    nodes,
    edges,
    input_data,
    shared_memory: bool = False,
):
    import asyncio

    async def _execute():
        return await executor.execute(
            nodes=nodes,
            edges=edges,
            input_data=input_data,
            shared_memory=shared_memory,
        )

    return asyncio.run(_execute())


if __name__ == "__main__":
    workflow()
