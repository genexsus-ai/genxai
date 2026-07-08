# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- FLOW graph node type — embed multi-agent flow patterns (critic review, ensemble voting, map-reduce, coordinator/worker, auction, p2p, round robin, parallel) as a single workflow node via the `FLOW_TYPES` registry.
- `ExecutionStore.delete()` removes run records from memory, SQL, and JSON persistence.
- MCP client for calling tools on external MCP servers, with server tools exposed as agent-usable proxy tools.
- Persistent agent memory across runs.
- Template expressions for passing data between workflow nodes.
- Subworkflow (subgraph) nodes with nested workflow definitions exposed as an `execute()` param.
- Per-node execution policies (retry, timeout, continue-on-error).

### Fixed
- LLM providers now lazily re-create a closed client (`_ensure_client`). `AgentRuntime.execute()` closes its provider after each call, so flows that reuse runtimes across iterations (critic review round 2, p2p rounds, batch execution) failed with "client not initialized".
- Runtime-orchestrated flows (Auction/CoordinatorWorker/CriticReview/EnsembleVoting/MapReduce/P2P) were uninstantiable (abstract `build_graph`).
- `__version__` resolved the wrong distribution name ("genxai" → "genxai-framework") and reported 0.0.0; CLI `--version` now reports the real version.

### Documentation
- Documented availability of production-grade runtime features (connectors, triggers, observability, security, CLI extensions, worker queue engine).
- Updated GenXBot docs to reflect full recipe-template integration: `recipe_id`/`recipe_inputs` rendering, blending recipe + agent-generated actions, deduplication, and fallback action guarantees.
- Added implementation/test references for recipe blending behavior in GenXBot docs (`orchestrator.py`, `routes_runs.py`, and orchestrator blend tests).
- Expanded GenXBot observability docs with structured hooks for plan latency, tool execution attempts, safety decisions, and retry/failure events.
- Added usage/setup examples for recipe-templated runs and observability verification endpoints.

## [0.1.6] - 2026-02-13
### Added
- LLM-based ranking utility with safe JSON parsing, repair logic, and heuristic fallback scoring.
- Opt-in agent config flag (`enable_llm_ranking`) and runtime tool ranking output (`tool_rankings`).
- Ranking utility tests covering valid JSON, repaired JSON, and heuristic fallback paths.
- Documentation updates and examples for LLM ranking usage and heuristic defaults.
