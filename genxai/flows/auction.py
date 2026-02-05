"""Auction flow orchestrator."""

from typing import Any, Dict, List, Optional

from genxai.core.agent.runtime import AgentRuntime
from genxai.flows.base import FlowOrchestrator


class AuctionFlow(FlowOrchestrator):
    """Agents bid to handle a task; highest bid executes."""

    def __init__(
        self,
        agents: List[Any],
        name: str = "auction_flow",
        llm_provider: Any = None,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        if state is None:
            state = {}
        state["input"] = input_data
        state.setdefault("bids", {})

        runtimes = {
            agent.id: AgentRuntime(agent=agent, llm_provider=self.llm_provider)
            for agent in self.agents
        }

        bid_task = state.get("bid_task", "Provide a numeric bid between 0 and 1")
        tasks = [
            self._execute_with_retry(
                runtimes[agent.id],
                task=bid_task,
                context=state,
            )
            for agent in self.agents
        ]
        results = await self._gather_tasks(tasks)
        for agent, bid_result in zip(self.agents, results):
            bid_value = 0.0
            try:
                bid_value = float(bid_result.get("output", 0))
            except (TypeError, ValueError, AttributeError):
                bid_value = 0.0
            state["bids"][agent.id] = bid_value

        if not state["bids"]:
            raise ValueError("AuctionFlow requires at least one bid")

        winner_id = max(state["bids"], key=state["bids"].get)
        winner_runtime = runtimes[winner_id]
        execution = await self._execute_with_retry(
            winner_runtime,
            task=state.get("task", "Execute the task"),
            context={**state, "winner_id": winner_id},
        )
        state["winner_id"] = winner_id
        state["winner_result"] = execution
        return state