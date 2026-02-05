"""Coordinator-worker flow orchestrator."""

from typing import Any, Dict, List, Optional

from genxai.core.agent.runtime import AgentRuntime
from genxai.flows.base import FlowOrchestrator


class CoordinatorWorkerFlow(FlowOrchestrator):
    """Coordinator assigns tasks to worker agents."""

    def __init__(
        self,
        agents: List[Any],
        name: str = "coordinator_worker_flow",
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
        state.setdefault("worker_results", [])

        if len(self.agents) < 2:
            raise ValueError("CoordinatorWorkerFlow requires at least two agents")

        coordinator = self.agents[0]
        workers = self.agents[1:]
        coordinator_runtime = AgentRuntime(agent=coordinator, llm_provider=self.llm_provider)
        worker_runtimes = {
            agent.id: AgentRuntime(agent=agent, llm_provider=self.llm_provider)
            for agent in workers
        }

        plan = await self._execute_with_retry(
            coordinator_runtime,
            task=state.get("task", "Break the task into worker assignments"),
            context=state,
        )
        state["plan"] = plan

        worker_task = state.get("worker_task", "Execute assigned task")
        tasks = [
            self._execute_with_retry(
                worker_runtimes[worker.id],
                task=worker_task,
                context={**state, "worker_id": worker.id},
            )
            for worker in workers
        ]
        results = await self._gather_tasks(tasks)
        for worker, result in zip(workers, results):
            state["worker_results"].append({"worker_id": worker.id, "result": result})

        return state