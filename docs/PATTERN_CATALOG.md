# GenXAI Pattern Catalog

This document consolidates the workflow/coordination patterns that GenXAI can handle in the OSS codebase.

> Scope: based on current implementations under `genxai/flows/` and documented examples in `examples/`.

---

## A) Built-in Flow Orchestrator Patterns (first-class)

These patterns are directly implemented as reusable flow classes.

| Pattern | What it does | Primary implementation | Example(s) |
|---|---|---|---|
| Round Robin / Sequential Chain | Executes agents in a fixed order | `genxai/flows/round_robin.py` (`RoundRobinFlow`) | `examples/code/flow_round_robin_example.py` |
| Parallel Execution | Fans out to multiple agents concurrently and joins outputs | `genxai/flows/parallel.py` (`ParallelFlow`) | `examples/code/flow_parallel_example.py` |
| Conditional Routing | Routes to one agent based on condition callback | `genxai/flows/conditional.py` (`ConditionalFlow`) | `examples/code/flow_conditional_example.py` |
| Intent/Rule-Based Routing | Deterministic routing via router function | `genxai/flows/router.py` (`RouterFlow`) | `examples/code/flow_router_example.py` |
| Selector-Based Dynamic Routing | Selects next agent hop-by-hop | `genxai/flows/selector.py` (`SelectorFlow`) | `examples/code/flow_selector_example.py` |
| Loop / Cyclic Iteration | Repeats execution until condition or max iterations | `genxai/flows/loop.py` (`LoopFlow`) | `examples/code/flow_loop_example.py` |
| Reflection / Critic-Review | Generator → critic feedback loop with bounded retries | `genxai/flows/critic_review.py` (`CriticReviewFlow`) | `examples/code/flow_critic_review_example.py` |
| Coordinator–Worker (Hierarchical) | Coordinator plans; workers execute (typically in parallel) | `genxai/flows/coordinator_worker.py` (`CoordinatorWorkerFlow`) | `examples/code/flow_coordinator_worker_example.py` |
| Map-Reduce | Multiple mappers + reducer aggregation | `genxai/flows/map_reduce.py` (`MapReduceFlow`) | `examples/code/flow_map_reduce_example.py` |
| Ensemble Voting | Runs multiple agents and aggregates via voting | `genxai/flows/ensemble_voting.py` (`EnsembleVotingFlow`) | `examples/code/flow_ensemble_voting_example.py` |
| Peer-to-Peer (P2P) | Decentralized agent collaboration with convergence/consensus checks | `genxai/flows/p2p.py` (`P2PFlow`) | `examples/code/flow_p2p_example.py` |
| Subworkflow Composition | Executes reusable pre-built graph workflows as subflows | `genxai/flows/subworkflow.py` (`SubworkflowFlow`) | `examples/code/flow_subworkflow_example.py` |
| Auction / Competitive Selection | Agents bid; best bid handles task | `genxai/flows/auction.py` (`AuctionFlow`) | `examples/code/flow_auction_example.py` |

---

## B) Canonical Graph Patterns (composable)

These are modeled directly via graph nodes/edges (and may overlap with flow classes).

| Pattern | How GenXAI handles it | Example(s) |
|---|---|---|
| Sequential Pipeline | Chain `Edge(source, target)` between agents | `examples/patterns/01_sequential_pattern.py` |
| Conditional Branching | Router/condition node with conditional edges | `examples/patterns/02_conditional_branching.py` |
| Parallel Split/Aggregate | Parallel edges or `metadata={"parallel": True}` fan-out | `examples/patterns/03_parallel_execution.py` |
| Coordinator–Delegator–Worker (CDW) | Hierarchical orchestration using coordinator/delegator/workers | `examples/patterns/04_coordinator_delegator_worker.py` |
| Cyclic/Iterative Refinement | Feedback loops with stop conditions and max iteration guards | `examples/patterns/05_cyclic_iterative.py` |
| Peer-to-Peer Collaboration | Direct agent-to-agent decentralized exchange | `examples/patterns/06_peer_to_peer.py` |

---

## C) Mapping to the “core six” patterns you asked about

| Requested pattern | GenXAI support |
|---|---|
| Orchestration | ✅ Graph engine + flow orchestrators |
| Reflection | ✅ `CriticReviewFlow` |
| Sequential Coordination | ✅ `RoundRobinFlow` + sequential graph chains |
| Intent-Based Routing | ✅ `RouterFlow` / `ConditionalFlow` |
| Parallel Execution | ✅ `ParallelFlow` + graph parallel edges |
| Prompt Chaining | ✅ Implemented as sequential multi-agent chains/graphs |

---

## Notes

- `docs/FLOWS.md` is the reference for flow orchestrator APIs.
- `examples/code/` demonstrates runnable flow-specific usage.
- `examples/patterns/` demonstrates pattern archetypes independent of a single flow wrapper.
- Prompt chaining is represented as composition of sequential steps rather than a dedicated class named `PromptChainingFlow`.
