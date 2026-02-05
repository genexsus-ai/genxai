"""Base orchestrator for composable flow patterns."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, List, Optional
from abc import ABC, abstractmethod

from genxai.core.agent.base import Agent
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import AgentNode


class FlowOrchestrator(ABC):
    """Base class for flow orchestrators.

    A flow orchestrator converts a list of agents into a Graph
    and executes it using the existing graph engine.
    """

    def __init__(
        self,
        agents: Iterable[Agent],
        name: str = "flow",
        llm_provider: Any = None,
        allow_empty_agents: bool = False,
        timeout_seconds: float = 120.0,
        retry_count: int = 3,
        backoff_base: float = 1.0,
        backoff_multiplier: float = 2.0,
        cancel_on_failure: bool = True,
    ) -> None:
        self.agents = list(agents)
        if not self.agents and not allow_empty_agents:
            raise ValueError("FlowOrchestrator requires at least one agent")

        self.name = name
        self.llm_provider = llm_provider
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier
        self.cancel_on_failure = cancel_on_failure

        for agent in self.agents:
            AgentRegistry.register(agent)

    @abstractmethod
    def build_graph(self) -> Graph:
        """Construct a Graph for this flow pattern."""

    async def run(
        self,
        input_data: Any,
        state: Optional[Dict[str, Any]] = None,
        max_iterations: int = 100,
    ) -> Dict[str, Any]:
        """Execute the flow graph with the provided input."""
        if state is None:
            state = {}
        state.setdefault(
            "execution_config",
            {
                "timeout_seconds": self.timeout_seconds,
                "retry_count": self.retry_count,
                "backoff_base": self.backoff_base,
                "backoff_multiplier": self.backoff_multiplier,
                "cancel_on_failure": self.cancel_on_failure,
            },
        )
        graph = self.build_graph()
        return await graph.run(
            input_data=input_data,
            max_iterations=max_iterations,
            state=state,
            llm_provider=self.llm_provider,
        )

    def _agent_nodes(self) -> List[AgentNode]:
        """Create AgentNode instances for each registered agent."""
        return [AgentNode(id=agent.id, agent_id=agent.id) for agent in self.agents]

    async def _execute_with_retry(
        self,
        runtime: Any,
        task: str,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a runtime task with retries and timeout."""
        delay = self.backoff_base
        for attempt in range(self.retry_count + 1):
            try:
                coro = runtime.execute(task=task, context=context)
                if self.timeout_seconds:
                    return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
                return await coro
            except asyncio.CancelledError:
                raise
            except Exception:
                if attempt >= self.retry_count:
                    raise
                await asyncio.sleep(delay)
                delay *= self.backoff_multiplier

    async def _gather_tasks(self, coros: List[Any]) -> List[Any]:
        """Run tasks concurrently, optionally canceling on first failure."""
        tasks = [asyncio.create_task(coro) for coro in coros]
        if not tasks:
            return []

        if not self.cancel_on_failure:
            return await asyncio.gather(*tasks, return_exceptions=True)

        results: List[Any] = [None] * len(tasks)
        index_map = {task: idx for idx, task in enumerate(tasks)}
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for task in done:
            idx = index_map[task]
            exc = task.exception()
            if exc:
                for pending_task in pending:
                    pending_task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                raise exc
            results[idx] = task.result()

        if pending:
            pending_results = await asyncio.gather(*pending, return_exceptions=True)
            for task, result in zip(pending, pending_results):
                results[index_map[task]] = result

        return results