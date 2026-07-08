# Agent Catalog

Every reusable agent and agent-team primitive in GenXAI, what it does, and
how to compose them into your own applications. All of these ship in the
`genxai` package — nothing here depends on the Workflow Studio.

Three kinds of building blocks, from lowest to highest level:

1. **Custom agents** — you define role/goal/backstory/tools; the framework runs them.
2. **Flow patterns** — pre-built multi-agent collaboration shapes you fill with your agents.
3. **The generation crew** — five specialized agents that turn natural language into executable workflows.

---

## 1. Custom agents (build-your-own)

Any agent is a config (`role`, `goal`, `backstory`, `llm_model`, `tools`,
`memory`, `agent_type`) executed by `AgentRuntime`, which assembles the
system prompt, calls the LLM (with native function-calling for tools), and
manages memory.

```python
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

agent = AgentFactory.create_agent(
    id="analyst",
    role="Financial Analyst",                    # "You are a {role}."
    goal="Assess the company's financial health", # "Your goal is: {goal}"
    backstory="A CFA with 15 years in equity research",  # "Background: ..."
    agent_type="deliberative",                   # adds think-before-acting instruction
    llm_model="claude-sonnet-5",
    tools=["web_scraper", "calculator"],         # names from the ToolRegistry
    memory_type="episodic",
)
result = await AgentRuntime(agent=agent).execute(task="Analyze ACME Corp Q3")
print(result["output"])
```

Where: `genxai/core/agent/base.py` (config/factory), `genxai/core/agent/runtime.py` (execution).

**Presets** (`genxai/agents/presets.py`):

| Preset | What it is | Use for |
|---|---|---|
| `AssistantAgent.create(id, goal, ...)` | Deliberative assistant with sensible defaults | General reasoning/answering agents |
| `UserProxyAgent.create(id, ...)` | Reactive agent meant to be paired with a human-input tool | Human-in-the-loop steps |

**Agent types** (changes the system-prompt instruction): `reactive` (default,
no extra instruction), `deliberative` (plan before acting), `learning`
(improve from feedback), `collaborative` (coordinate with other agents).

---

## 2. Flow patterns (agent teams)

Pre-built collaboration shapes in `genxai/flows/`. Each takes a list of your
agents and orchestrates them — with retries, timeouts, and concurrency
handled for you. Addressable by name via `FLOW_TYPES`, embeddable as a
single node inside any workflow (`FlowNode`), and usable directly:

```python
from genxai.flows import CriticReviewFlow

flow = CriticReviewFlow([writer_agent, critic_agent], llm_provider=provider)
state = await flow.run("Write a launch announcement for our new API")
```

| Pattern (`FLOW_TYPES` name) | Agent order | What happens | Use for |
|---|---|---|---|
| `round_robin` | any | Agents take turns responding in order | Panel discussions, iterative building |
| `parallel` | any | All agents work the same task concurrently | Independent perspectives, speed |
| `coordinator_worker` | 1st = coordinator | Coordinator plans; the rest execute in parallel | Fan-out work with a planning step |
| `delegator_worker` | 1st = delegator | Delegator emits typed work packets routed to workers by tag, executed in dependency waves; each packet gets its dependencies' results | Heterogeneous specialists, LLM-driven task routing |
| `critic_review` | 1st = generator, 2nd = critic | Draft → critique → redraft until accepted or max iterations | Quality-gated content, code review loops |
| `ensemble_voting` | any | All answer independently; majority wins | Reliability on classification/decisions |
| `map_reduce` | last = reducer | All but the last work in parallel; the last merges | Chunked processing + synthesis |
| `auction` | any | Agents bid on the task; highest bidder executes | Cost/fit-based task assignment |
| `p2p` | any | Peer-to-peer message exchange until convergence | Negotiation, consensus building |

`delegator_worker` specifics: workers are addressed by
`metadata={"worker_tag": "..."}` (falls back to role); the delegator's output
is schema-validated (`DelegationPlan`) with error-feedback retries. See
`genxai/flows/delegator.py`.

Runnable examples for every pattern: `examples/code/flow_*_example.py` and
`examples/patterns/`. Full docs: [FLOWS.md](./FLOWS.md).

---

## 3. The workflow-generation crew

Five specialized agents in `genxai/builder/` that collaborate to turn a
natural-language request into an executable workflow document. Unlike the
agents above, these are schema-constrained LLM calls (via
`genxai.utils.structured.generate_structured`) — every output is validated
against a Pydantic model with automatic repair retries, and every capability
they mention is checked against a `CapabilityCatalog`.

| Agent | Function | Input → Output | Prompt constant |
|---|---|---|---|
| **Planner** | `plan_workflow()` in `builder/planner.py` | request + catalog (+ memory recall) → `WorkflowPlan` (steps, dependencies, trigger, open questions) | `PLANNER_SYSTEM_PROMPT` |
| **Delegator** | `delegate_plan()` in `builder/crew.py` | plan → `DelegationPlan` (work packets routed to designer workers); deterministic fallback on failure | `DELEGATOR_SYSTEM_PROMPT` |
| **Agent designer** | `run_agent_designer()` in `builder/crew.py` | assigned agent steps → `AgentSpec` per step (role, goal, backstory, temperature, tools) | `AGENT_DESIGNER_SYSTEM_PROMPT` |
| **Node designer** | `run_node_designer()` in `builder/crew.py` | assigned tool/decision/loop/flow steps → `NodeSpec` per step (capability, params, conditions) | `NODE_DESIGNER_SYSTEM_PROMPT` |
| **Reviewer** | `review_plan()` in `builder/crew.py` | request + refined plan → `ReviewVerdict` (approved / concrete issues); rejections re-enter planning | `REVIEWER_SYSTEM_PROMPT` |

Entry points, lowest effort first:

```python
from genxai.builder import (
    generate_workflow,        # planner only (fast, cheap)
    crew_generate_workflow,   # full crew (delegation + design + review)
    refine_workflow,          # modify an existing workflow by instruction
    plan_workflow,            # just the plan, no compilation
    compile_plan,             # deterministic plan -> workflow dict (no LLM)
    build_capability_catalog, # what the agents are allowed to use
    GenerationMemory,         # optional: learn from accepted generations
    evaluate_generation,      # measure validity + buildability over prompts
)
```

The generated workflow dict runs unchanged on `WorkflowExecutor` (or
`genxai workflow run` after dumping to YAML). Full guide:
[WORKFLOW_GENERATION.md](./WORKFLOW_GENERATION.md).

---

## Composing them: application recipes

**Recipe 1 — Chat-to-automation bot** (Slack/Teams/CLI): pipe user messages
into the generation crew; execute the result immediately.

```python
catalog = build_capability_catalog()          # or inject your app's inventory
result = await crew_generate_workflow(user_message, llm_provider=provider,
                                      catalog=catalog, memory=memory)
run = await execute_workflow_async(result.workflow["graph"]["nodes"], ...)
```

**Recipe 2 — Domain copilot with a restricted toolbox**: give the crew only
your domain's capabilities so every generated workflow stays inside them.

```python
catalog = build_capability_catalog(
    include_tools=False,
    extra_sections={"tool": [{"name": "crm.lookup", "description": "..."},
                              {"name": "crm.update", "description": "..."}]},
)
```

**Recipe 3 — Quality-gated content pipeline**: your own agents inside a
`critic_review` flow, embedded as one node of a larger workflow (`FlowNode`
with `flow_type="critic_review"`).

**Recipe 4 — Research swarm with a routing lead**: `DelegatorFlow` with
tagged specialists (`researcher`, `analyst`, `writer`); the delegator routes
packets and dependent packets receive upstream results automatically.

**Recipe 5 — Reliable classifier**: three differently-prompted agents in an
`ensemble_voting` flow; majority answer wins.

**Recipe 6 — Self-improving generator**: pass a `GenerationMemory` to the
crew and call `memory.mark_accepted(result.generation_id)` whenever a user
keeps the output — future similar requests recall accepted plans as examples.

---

## Choosing the right level

| You want to… | Reach for |
|---|---|
| Add one smart step to existing code | A custom agent + `AgentRuntime` |
| Make several agents collaborate on a task | A flow pattern from `FLOW_TYPES` |
| Route heterogeneous work to specialists dynamically | `DelegatorFlow` |
| Turn user language into runnable automation | `generate_workflow` / `crew_generate_workflow` |
| Let users iterate on generated automation | `refine_workflow` |
| Constrain what generated automation can do | `build_capability_catalog(extra_sections=...)` |
| Measure/regress generation quality | `evaluate_generation` |

A worked reference implementation of all of this wired into a real product —
catalog injection, SSE progress, draft review, acceptance learning — is the
Workflow Studio (`applications/workflow_studio/`, see
`backend/app/generation.py`).
