"""Run lightweight GenXAI performance benchmarks."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time
from typing import Any, Dict, List

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin.computation.calculator import CalculatorTool


def _build_graph(agent_id: str) -> Graph:
    graph = Graph(name="benchmark_workflow")
    graph.add_node(InputNode(id="start"))
    graph.add_node(AgentNode(id="agent", agent_id=agent_id))
    graph.add_node(OutputNode(id="end"))
    graph.add_edge(Edge(source="start", target="agent"))
    graph.add_edge(Edge(source="agent", target="end"))
    return graph


async def _execute_workflow(
    agent_id: str,
    llm_model: str,
    provider: str,
    timeout: int,
) -> Dict[str, Any]:
    agent = AgentFactory.create_agent(
        id=agent_id,
        role="Benchmark Agent",
        goal="Respond quickly and consistently",
        llm_model=llm_model,
        tools=["calculator"],
        max_execution_time=timeout,
    )

    ToolRegistry.register(CalculatorTool())

    runtime = AgentRuntime(agent=agent)
    graph = _build_graph(agent_id=agent.id)

    start_time = time.time()
    result = await runtime.execute(
        task="Compute 21 * 2 and summarize in one sentence.",
        context={"provider": provider},
    )
    latency = time.time() - start_time

    return {
        "latency": latency,
        "tokens": result.get("tokens_used", 0),
        "status": result.get("status", "unknown"),
    }


async def run_benchmark(workflows: int, parallel: int, model: str, provider: str, timeout: int) -> None:
    sem = asyncio.Semaphore(parallel)
    results: List[Dict[str, Any]] = []

    async def _bounded(i: int) -> None:
        async with sem:
            result = await _execute_workflow(
                agent_id=f"bench_agent_{i}",
                llm_model=model,
                provider=provider,
                timeout=timeout,
            )
            results.append(result)

    await asyncio.gather(*[_bounded(i) for i in range(workflows)])

    latencies = [r["latency"] for r in results]
    success_rate = sum(1 for r in results if r["status"] == "completed") / len(results)
    avg_latency = statistics.mean(latencies)
    p50 = statistics.quantiles(latencies, n=100)[49]
    p95 = statistics.quantiles(latencies, n=100)[94]
    p99 = statistics.quantiles(latencies, n=100)[98]

    print("Benchmark Results")
    print("-----------------")
    print(f"Workflows: {workflows}")
    print(f"Parallelism: {parallel}")
    print(f"Success rate: {success_rate:.0%}")
    print(f"Avg latency: {avg_latency:.2f}s")
    print(f"P50: {p50:.2f}s, P95: {p95:.2f}s, P99: {p99:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="GenXAI benchmark runner")
    parser.add_argument("--workflows", type=int, default=50)
    parser.add_argument("--parallel", type=int, default=10)
    parser.add_argument("--model", type=str, default="gpt-4")
    parser.add_argument("--provider", type=str, default="openai")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.workflows, args.parallel, args.model, args.provider, args.timeout))


if __name__ == "__main__":
    main()
