"""Subworkflow flow orchestrator."""

from typing import Any, Dict, Optional

from genxai.core.graph.engine import Graph
from genxai.flows.base import FlowOrchestrator


class SubworkflowFlow(FlowOrchestrator):
    """Execute a pre-built subgraph as a flow."""

    def __init__(
        self,
        graph: Graph,
        name: str = "subworkflow_flow",
        llm_provider: Any = None,
    ) -> None:
        super().__init__(agents=[], name=name, llm_provider=llm_provider, allow_empty_agents=True)
        self.graph = graph

    def build_graph(self) -> Graph:
        return self.graph

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        return await self.graph.run(
            input_data=input_data,
            state=state,
            max_iterations=max_iterations,
            llm_provider=self.llm_provider,
        )