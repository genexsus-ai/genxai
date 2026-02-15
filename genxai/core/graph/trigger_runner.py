"""Trigger-driven workflow execution utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from genxai.core.graph.executor import WorkflowExecutor

try:  # enterprise-only feature
    from enterprise.genxai.triggers.base import TriggerEvent  # type: ignore
except Exception:  # pragma: no cover
    TriggerEvent = Any  # type: ignore

logger = logging.getLogger(__name__)


class TriggerWorkflowRunner:
    """Bind trigger events to workflow execution."""

    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.executor = WorkflowExecutor(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )

    async def handle_event(self, event: TriggerEvent) -> Dict[str, Any]:
        """Execute the workflow using the trigger event payload as input."""
        logger.info("Trigger event received: %s", event.trigger_id)
        input_data = event.payload or {}
        result = await self.executor.execute(
            nodes=self.nodes,
            edges=self.edges,
            input_data=input_data,
        )
        return result