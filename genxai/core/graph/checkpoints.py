"""Workflow checkpoint persistence utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json

from genxai.core.graph.nodes import NodeStatus


@dataclass
class WorkflowCheckpoint:
    """Snapshot of a workflow run."""

    name: str
    workflow: str
    created_at: str
    state: Dict[str, Any]
    node_statuses: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "workflow": self.workflow,
            "created_at": self.created_at,
            "state": self.state,
            "node_statuses": self.node_statuses,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowCheckpoint":
        return cls(
            name=data["name"],
            workflow=data["workflow"],
            created_at=data["created_at"],
            state=data.get("state", {}),
            node_statuses=data.get("node_statuses", {}),
        )


class WorkflowCheckpointManager:
    """Persist workflow checkpoints to disk."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def save(self, checkpoint: WorkflowCheckpoint) -> Path:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path = self.base_dir / f"checkpoint_{checkpoint.name}.json"
        path.write_text(json.dumps(checkpoint.to_dict(), indent=2, default=str))
        return path

    def load(self, name: str) -> WorkflowCheckpoint:
        path = self.base_dir / f"checkpoint_{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        data = json.loads(path.read_text())
        return WorkflowCheckpoint.from_dict(data)


def create_checkpoint(
    name: str,
    workflow: str,
    state: Dict[str, Any],
    node_statuses: Dict[str, NodeStatus],
) -> WorkflowCheckpoint:
    """Create a checkpoint object from current workflow state."""
    return WorkflowCheckpoint(
        name=name,
        workflow=workflow,
        created_at=datetime.now().isoformat(),
        state=state,
        node_statuses={node_id: status.value for node_id, status in node_statuses.items()},
    )