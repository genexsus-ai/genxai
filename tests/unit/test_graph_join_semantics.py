"""Tests for graph join semantics, dead-branch skipping, and loop bodies."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import Node, NodeConfig, NodeStatus, NodeType
from genxai.core.graph.edges import Edge


class ProbeGraph(Graph):
    """Graph that records execution order and the state each node observed."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.exec_order = []
        self.observed_state = {}

    async def _execute_node_logic(self, node, state, max_iterations):
        self.exec_order.append(node.id)
        if node.id == "b":
            await asyncio.sleep(0.02)
        self.observed_state[node.id] = set(state.keys())
        return f"result_{node.id}"


def _condition_node(node_id: str) -> Node:
    return Node(id=node_id, type=NodeType.CONDITION, config=NodeConfig(type=NodeType.CONDITION))


@pytest.mark.asyncio
async def test_diamond_join_waits_for_all_parents():
    """A join node must run once, after every taken incoming branch."""
    graph = ProbeGraph("diamond")
    for node_id in ["a", "b", "c", "d"]:
        graph.add_node(_condition_node(node_id))
    graph.add_edge(Edge(source="a", target="b", metadata={"parallel": True}))
    graph.add_edge(Edge(source="a", target="c", metadata={"parallel": True}))
    graph.add_edge(Edge(source="b", target="d"))
    graph.add_edge(Edge(source="c", target="d"))

    await graph.run(input_data={})

    assert graph.exec_order.count("d") == 1
    assert {"b", "c"} <= graph.observed_state["d"]


@pytest.mark.asyncio
async def test_dead_branch_is_skipped_and_join_still_resolves():
    """An untaken branch is marked SKIPPED and does not deadlock the join."""
    graph = ProbeGraph("branch")
    for node_id in ["inp", "a", "b", "out"]:
        graph.add_node(_condition_node(node_id))
    graph.add_edge(Edge(source="inp", target="a", condition=lambda s: True))
    graph.add_edge(Edge(source="inp", target="b", condition=lambda s: False))
    graph.add_edge(Edge(source="a", target="out"))
    graph.add_edge(Edge(source="b", target="out"))

    await graph.run(input_data={})

    assert "out" in graph.exec_order
    assert "b" not in graph.exec_order
    assert graph.nodes["b"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_cycle_back_edge_does_not_deadlock_join():
    """A back edge must not be counted in join readiness."""
    graph = ProbeGraph("cycle")
    for node_id in ["a", "b", "c"]:
        graph.add_node(_condition_node(node_id))
    graph.add_edge(Edge(source="a", target="b"))
    graph.add_edge(Edge(source="b", target="c"))
    graph.add_edge(Edge(source="c", target="b"))

    await graph.run(input_data={})

    assert graph.exec_order == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_graph_is_reusable_across_runs():
    """Node statuses reset on fresh runs, so a Graph can be run repeatedly."""
    graph = ProbeGraph("reuse")
    graph.add_node(_condition_node("a"))
    graph.add_node(_condition_node("b"))
    graph.add_edge(Edge(source="a", target="b"))

    state1 = await graph.run(input_data="first")
    state2 = await graph.run(input_data="second")

    assert list(state1.get("node_results", {}).keys()) == ["a", "b"]
    assert list(state2.get("node_results", {}).keys()) == ["a", "b"]


@pytest.mark.asyncio
async def test_loop_node_executes_tool_body():
    """LOOP nodes run their configured body every iteration."""
    calls = []

    fake_tool = MagicMock()

    async def fake_execute(**kwargs):
        calls.append(kwargs)
        result = MagicMock()
        result.model_dump.return_value = {"ok": True, "call": len(calls)}
        return result

    fake_tool.execute = fake_execute

    with patch("genxai.core.graph.engine.ToolRegistry.get", return_value=fake_tool):
        graph = Graph("loop")
        graph.add_node(
            Node(
                id="loop1",
                type=NodeType.LOOP,
                config=NodeConfig(
                    type=NodeType.LOOP,
                    data={
                        "max_iterations": 3,
                        "body": {"type": "tool", "tool_name": "probe", "tool_params": {"x": 1}},
                    },
                ),
            )
        )
        state = await graph.run(input_data={})

    assert len(calls) == 3
    assert state["loop1"]["iterations"] == 3
    assert state["loop_loop1_last_result"] == {"ok": True, "call": 3}


@pytest.mark.asyncio
async def test_loop_node_condition_exit():
    """LOOP nodes exit early when the condition state key becomes truthy."""
    graph = Graph("loop_cond")
    graph.add_node(
        Node(
            id="loop2",
            type=NodeType.LOOP,
            config=NodeConfig(
                type=NodeType.LOOP,
                data={"max_iterations": 10, "condition": "loop_loop2_iteration"},
            ),
        )
    )
    state = await graph.run(input_data={})

    assert state["loop2"]["iterations"] == 1
