"""Selector-based flow orchestrator."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import AgentNode
from genxai.flows.base import FlowOrchestrator


class SelectorFlow(FlowOrchestrator):
    """Route to the next agent using a selector function.

    The selector function returns the agent ID to execute next.
    """

    def __init__(
        self,
        agents: List[Any],
        selector: Callable[[Dict[str, Any], List[str]], str],
        name: str = "selector_flow",
        llm_provider: Any = None,
        max_hops: int = 1,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)
        self.selector = selector
        self.max_hops = max_hops

    def build_graph(self) -> Graph:
        graph = Graph(name=self.name)
        nodes: List[AgentNode] = self._agent_nodes()

        for node in nodes:
            graph.add_node(node)

        return graph

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        graph = self.build_graph()
        if state is None:
            state = {}

        state["input"] = input_data
        agent_ids = [agent.id for agent in self.agents]

        for hop in range(self.max_hops):
            selected = self.selector(state, agent_ids)
            if selected not in agent_ids:
                raise ValueError(
                    f"SelectorFlow returned unknown agent id '{selected}'."
                )

            state["next_agent"] = selected
            state["selector_hop"] = hop + 1
            await graph._execute_node(selected, state, max_iterations)

        return state