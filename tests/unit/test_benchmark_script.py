"""Smoke test for benchmark script utilities."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_benchmark_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "benchmarks" / "run_benchmark.py"
    spec = importlib.util.spec_from_file_location("genxai_benchmark", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_benchmark_graph_builds() -> None:
    module = _load_benchmark_module()
    graph = module._build_graph("bench-agent")
    assert graph.name == "benchmark_workflow"
    assert "start" in graph.nodes
    assert "agent" in graph.nodes
    assert "end" in graph.nodes
    assert len(graph.edges) == 2
