"""MapReduce flow orchestrator."""

import asyncio
from typing import Any, Dict, List, Optional

from genxai.core.agent.runtime import AgentRuntime
from genxai.flows.base import FlowOrchestrator


class MapReduceFlow(FlowOrchestrator):
    """Run multiple agents in map phase, then summarize with reducer."""

    def __init__(
        self,
        agents: List[Any],
        name: str = "map_reduce_flow",
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
        state.setdefault("map_results", [])

        if len(self.agents) < 2:
            raise ValueError("MapReduceFlow requires at least two agents")

        *mappers, reducer = self.agents
        mapper_runtimes = {
            agent.id: AgentRuntime(agent=agent, llm_provider=self.llm_provider)
            for agent in mappers
        }
        reducer_runtime = AgentRuntime(agent=reducer, llm_provider=self.llm_provider)

        map_task = state.get("map_task", "Process shard")
        tasks = [
            self._execute_with_retry(
                mapper_runtimes[mapper.id],
                task=map_task,
                context={**state, "mapper_id": mapper.id},
            )
            for mapper in mappers
        ]
        results = await self._gather_tasks(tasks)
        for mapper, result in zip(mappers, results):
            state["map_results"].append({"mapper_id": mapper.id, "result": result})

        reduce_result = await self._execute_with_retry(
            reducer_runtime,
            task=state.get("reduce_task", "Summarize map results"),
            context={**state, "map_results": state["map_results"]},
        )
        state["reduce_result"] = reduce_result
        return state