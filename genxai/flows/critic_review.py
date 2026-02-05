"""Critic review flow orchestrator."""

from typing import Any, Dict, List, Optional

from genxai.core.agent.runtime import AgentRuntime
from genxai.flows.base import FlowOrchestrator


class CriticReviewFlow(FlowOrchestrator):
    """Generator -> critic -> revise loop with bounded iterations."""

    def __init__(
        self,
        agents: List[Any],
        name: str = "critic_review_flow",
        llm_provider: Any = None,
        max_iterations: int = 3,
    ) -> None:
        super().__init__(agents=agents, name=name, llm_provider=llm_provider)
        self.max_iterations = max_iterations

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        if state is None:
            state = {}
        state["input"] = input_data
        state.setdefault("drafts", [])

        if len(self.agents) < 2:
            raise ValueError("CriticReviewFlow requires at least two agents")

        generator = self.agents[0]
        critic = self.agents[1]
        gen_runtime = AgentRuntime(agent=generator, llm_provider=self.llm_provider)
        critic_runtime = AgentRuntime(agent=critic, llm_provider=self.llm_provider)

        draft = None
        for _ in range(self.max_iterations):
            gen_result = await self._execute_with_retry(
                gen_runtime,
                task=state.get("task", "Generate a draft"),
                context={**state, "draft": draft},
            )
            draft = gen_result.get("output")
            state["drafts"].append(draft)

            critique = await self._execute_with_retry(
                critic_runtime,
                task=state.get("critic_task", "Critique the draft"),
                context={**state, "draft": draft},
            )
            state["last_critique"] = critique

            if state.get("accept", False):
                break

        state["final"] = draft
        return state