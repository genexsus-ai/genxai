# Data Science App — Design

Status: **v1 fully implemented** (interactive analyses: agent loop, charts,
rerun-all, cell->dataset, scheduled reports, ML primitives).
**v2 proposed below: Experiments — a multi-agent data science crew.**
Scope: the third GenXAI app — agent-driven data analysis over the shared
data catalog. Not an embedded Jupyter: every "cell" is a question a person
asks; an agent plans, executes read-only SQL, and narrates.

## Why this shape

Two archetypes were considered:

1. **Embedded notebooks** (Python cells, kernel per user): maximum power,
   but requires a sandboxed execution environment, package management, and
   a security model for arbitrary code — months of infrastructure that
   reimplements Jupyter, which users already have (and which the catalog's
   Parquet export + HTTP API already feed).
2. **Agent-driven analysis** (this design): the unit of work is a
   *question*. An agent — given the source's schema and statistical
   profile — writes validated read-only DuckDB SQL, the platform executes
   it, and the agent interprets the result. Every step is inspectable SQL,
   not opaque model output. No sandbox is needed because the execution
   surface is the same read-only federated-SQL machinery Analytics already
   uses.

The second composes everything that exists (catalog, DuckDB federation,
profiles, agents, datasets) and is differentiated: n8n cannot do it and
Jupyter does not do it.

## Core concept: Analyses and Cells

An **Analysis** is a persistent, re-runnable document bound to one or more
catalog sources:

```json
{
  "id": "…",
  "name": "Q3 revenue investigation",
  "sources": {"orders": "<source-id>", "regions": "dataset:regions"},
  "cells": [ …ordered Cell list… ],
  "created_at": "…", "updated_at": "…"
}
```

A **Cell** is one question and its answer:

```json
{
  "id": "…",
  "question": "Which region's revenue is declining month over month?",
  "sql": "SELECT region, date_trunc('month', …) …",   // agent-written, validated
  "columns": ["region", "month", "revenue", "delta"],
  "result_rows": [ …capped snapshot (≤200 rows) for display… ],
  "row_count": 14,
  "chart": {"type": "bar", "x": "region", "y": "delta"},   // agent-suggested, optional
  "narrative": "West region declined 3 months straight (−12%, −8%, −5%)…",
  "status": "ok" | "error",
  "error": null,
  "created_at": "…", "ran_at": "…"
}
```

Key property: **cells store the SQL, not the data.** The result snapshot is
a display cache; *Rerun* re-executes against current data. That makes an
analysis a living report, and "Rerun all" turns it into a refreshable
dashboard with provenance.

## The agent loop

`POST /analyses/{id}/cells {question}`:

1. **Context assembly** — for each bound source: name/alias, schema,
   profile (the per-column statistics), plus a compact summary of prior
   cells (question + narrative + SQL) so follow-up questions compose
   ("now break that down by product").
2. **Plan** — one LLM call returns structured JSON:
   `{sql, chart: {type, x, y} | null, narrative_plan}` . SQL must reference
   only the bound aliases.
3. **Validate & execute** — `validate_readonly_sql` (single SELECT/WITH),
   then execute with the existing `FederatedAdapter` machinery (aliases →
   loaded tables, 50k rows/source cap). On SQL error the agent gets the
   error text and retries (max 3 attempts) — self-repair, recorded in the
   cell.
4. **Interpret** — second LLM call sees the question + result rows (capped)
   and writes the narrative: findings, caveats, suggested next question.
5. **Persist** the cell; the frontend renders table + chart + narrative.

Model resolution reuses `_resolve_model_and_key` (same keys as generation
and Ask AI). Failure modes are first-class: a cell with `status: error`
shows the attempted SQL and the error — editable and re-runnable by hand.

### Manual mode

A cell can also be created with explicit SQL (no agent) — the escape hatch
for users who know exactly what they want, and the edit path for agent
cells ("fix the SQL and rerun"). Same validation, same rendering.

## Storage

`analyses` table in the existing `datasets.db` (id, name, sources JSON,
cells JSON, timestamps). Cells are embedded — an analysis is a document,
not a graph; tens of cells × small snapshots stay well under SQLite
comfort. Version history piggybacks later if needed (same snapshot trick
as workflows).

## API

```
GET    /datascience/analyses
POST   /datascience/analyses            {name, sources: {alias: source_id}}
GET    /datascience/analyses/{id}
DELETE /datascience/analyses/{id}
PATCH  /datascience/analyses/{id}       {name?, sources?}
POST   /datascience/analyses/{id}/cells         {question}            # agent
POST   /datascience/analyses/{id}/cells/manual  {question?, sql}      # manual
POST   /datascience/analyses/{id}/cells/{cell_id}/rerun
PATCH  /datascience/analyses/{id}/cells/{cell_id}   {sql?, question?} # edit + rerun
DELETE /datascience/analyses/{id}/cells/{cell_id}
POST   /datascience/analyses/{id}/materialize/{cell_id}  {dataset}    # cell result -> dataset
```

## Frontend (the Data Science sidebar app)

- **Analyses list** (left rail, like Sources): name, source count, cell
  count, updated.
- **Analysis view**: bound sources as chips (add/remove via the catalog
  picker); a timeline of cells — each rendered as question → chart/table →
  narrative, with rerun / edit-SQL / delete / "→ dataset" actions; a
  composer at the bottom ("Ask about this data…") with a manual-SQL toggle.
- Charts reuse the validated palette and bar/table forms from Analytics;
  the agent's chart suggestion is constrained to shapes the UI renders
  (bar, line over an ordered column, table).

## Reproducibility & the loop back into the platform

- **Cell → dataset**: materialize any cell's result as a dataset (one
  call to `dataset_write` semantics) — feature tables and cleaned frames
  become first-class sources for further analysis or workflows.
- **Analysis → scheduled report** (P3): generate a workflow (like source
  materialization does) that reruns all cells on a schedule and emails /
  Slacks the narratives — reusing the connector + trigger machinery.

## Security

- Agent-generated SQL passes the same read-only single-statement gate as
  custom SQL sources; execution is in-memory DuckDB over capped loads —
  no write path exists.
- The LLM sees schemas, profiles, and capped result rows — the same
  exposure Ask AI already has.

## Phasing

| Phase | Contents |
|---|---|
| P1 | Analysis/cell store + agent loop (plan → validate → execute → interpret, retries) + manual cells + rerun + DS app UI (list, timeline, composer, tables) |
| P2 | Chart rendering from agent suggestions, edit-SQL flow, "Rerun all", cell → dataset materialization |
| P3 | Scheduled report workflows, sklearn primitives (fit/predict tools + model registry, predictions → datasets), cross-analysis references |

## Non-goals

- Arbitrary Python execution (revisit only with real sandboxing).
- Real-time collaborative editing (single-tenant studio).
- AutoML — the ML phase is deliberately "a few honest primitives," not a
  model zoo.

---

# v2: Experiments — the multi-agent data science crew

Status: **v2-P1 + v2-P2 implemented** — full pipeline: Planning, Exploration, Cleaning, Feature Engineering, Model Algorithm (spec or Python code), Cross-Validation, Test (holdout + predictions dataset), Visualization (matplotlib code stages), Metric Performance (report + ship/iterate/abandon), Programming and Code Review throughout; code-stage runtime with the ./data parquet in / ./out figures+datasets+model out contract. v2-P3 pending: human gates, experiment comparison, project export.

v1's analyses answer *questions* with a fixed two-agent pipeline (SQL
Planner → Insight Narrator). v2 adds **Experiments**: the user states an
*objective* ("predict churn from `customers`", "understand what drives
returns") and a **crew of specialist agents** runs the full data-science
lifecycle, producing inspectable artifacts at every stage. Interactive
analyses stay as they are — Experiments are the second mode, not a
replacement.

## Artifact policy: declarative first, Python where it earns it

Two artifact tiers, both reviewed before execution and both replayable:

1. **Declarative artifacts** (default wherever they suffice): read-only
   DuckDB SQL for exploration/cleaning/features, train/eval specs for the
   built-in model primitives. Cheapest to validate, fastest to run.
2. **Python code stages** — for what SQL and specs cannot do:
   **visualization** (matplotlib figures), **custom model development**
   (free-form sklearn pipelines, custom preprocessing), and advanced
   statistics. The framework's subprocess executor (`code_executor`)
   already exists; experiments use a hardened variant with a strict I/O
   contract:

   - **Inputs**: the platform materializes each bound source/stage
     dataset as `./data/<alias>.parquet` in a temp workdir; the script
     receives *data, never credentials* (environment scrubbed,
     `MPLBACKEND=Agg`, wall-clock timeout, output-size caps).
   - **Outputs**: the script writes to `./out/` — `figures/*.png` land in
     the file store and render in the experiment timeline;
     `datasets/*.parquet|csv` become datasets; `model.joblib` +
     `metrics.json` register in the model registry; the stdout tail is
     recorded on the stage.
   - **Review**: the Code Review Agent gates every script (imports
     against an allowlist — pandas/numpy/sklearn/matplotlib/scipy/stdlib
     — plus intent and leakage checks), and the optional human gate can
     require your approval before any code runs.
   - **Scope**: enabled in the self-hosted studio by default (precedent:
     n8n's Code node), disable with `GENXAI_DISABLE_CODE_STAGES=1`.
     This is process isolation on your own machine, not a hostile-tenant
     sandbox — the review gate, not the subprocess, is the primary
     control. Studio adds pandas, matplotlib, and pyarrow to
     requirements for these stages.

Exported experiments bundle everything — SQL, specs, and code stages —
as a runnable Python project, so the escape hatch to your own Jupyter is
always one download away.

## The crew

Built on `genxai.flows` patterns (delegator + critic_review), mirroring
the proven `builder.crew` architecture:

| Agent | Role | Artifact it produces |
|---|---|---|
| **Planning Agent** | Decomposes the objective into a staged pipeline; picks which specialists run and in what order; sets the target column & task type (regression / classification / descriptive) | The experiment plan (stage list with goals) |
| **Data Exploration Agent** | EDA over schema + profile: distributions, correlations (SQL), missingness map, target balance | Exploration cells (SQL + findings) feeding later stages |
| **Data Cleaning Agent** | Dedupe, null strategy, type casts, outlier filters — expressed as one SQL transformation | `<exp>_clean` dataset (materialized SQL) |
| **Feature Engineering Agent** | Ratios, buckets, date parts, joins/aggregations over cleaned data | `<exp>_features` dataset + feature dictionary |
| **Model Algorithm Agent** | Chooses model family from task type + data shape; picks the fast path (train spec on built-in primitives) or a Python code stage for custom pipelines | Train spec **or** model-development code stage |
| **Cross-Validation Agent** | k-fold CV over candidate specs (extends `ml.py` with `cross_validate`); flags overfitting via train/val gap | CV report per candidate |
| **Test Agent** | Final holdout evaluation of the chosen model on untouched data | Test metrics + prediction sample dataset |
| **Metric Performance Agent** | Interprets all metrics in business terms; compares candidates; recommends ship / iterate / abandon | The experiment report (markdown) |
| **Visualization Agent** | Turns findings into matplotlib figures (distributions, model diagnostics, feature importance) via code stages | `figures/*.png` in the timeline |
| **Programming Agent** | The shared "hands": turns every specialist's intent into concrete SQL / specs / Python code stages (specialists decide *what*, it writes *how*) | All SQL, spec, and code artifacts |
| **Code Review Agent** | Critic gate on every artifact *before execution*: SQL correctness vs. intent, leakage checks (target in features, post-outcome columns), spec sanity | Approve / revise verdicts (max 2 revision rounds) |

Two structural agents (Planning, Code Review) wrap the specialist chain;
the Programming Agent is the single writer so style and validation stay
uniform. Every specialist→programmer→reviewer exchange is the
`critic_review` flow; the Planning Agent's routing is the `delegator`
flow.

## Execution model

An **Experiment** runs as a background job (the run-manager pattern:
submit → poll/stream stage events), because a full pipeline takes
minutes, not seconds:

```
objective ──▶ PLAN ──▶ EXPLORE ──▶ CLEAN ──▶ FEATURES ──▶ MODEL SELECT
                                                        ──▶ CROSS-VALIDATE
                                                        ──▶ TEST ──▶ REPORT
```

- Each stage: specialist proposes → Programming Agent drafts artifact →
  Code Review Agent verdicts → (revise ≤2×) → platform executes/
  materializes → stage recorded with its artifact, verdict trail, and
  status. Failures stop the pipeline with everything up to that point
  preserved and individually re-runnable.
- **Human gates (optional per experiment)**: pause before materializing
  the cleaned dataset and before training — reusing the existing
  human-input machinery from workflows.
- Artifacts land in existing stores: datasets (`<exp>_clean`,
  `<exp>_features`, `<exp>_predictions`), the model registry, and the
  experiment document itself (an `experiments` table beside `analyses`).
- Reruns: an experiment replays its recorded artifacts against current
  data (like Rerun-all for analyses) — retraining and re-evaluating
  without re-planning, unless the user asks for a fresh plan.

## Framework additions required (small)

- `ml.py`: `cross_validate(spec, k)` via `sklearn.model_selection`
  (cross_val_score / train-val gap), and metrics for candidate
  comparison. Everything else — flows, HITL, datasets, models, file
  store, run events — already exists.

## API (v2)

```
POST /datascience/experiments {objective, source, target?, human_gates?}
GET  /datascience/experiments            # list with stage progress
GET  /datascience/experiments/{id}       # stages, artifacts, verdicts
POST /datascience/experiments/{id}/resume     # answer a human gate
POST /datascience/experiments/{id}/rerun
DELETE /datascience/experiments/{id}
```

## UI (v2)

Experiments tab beside Analyses: objective composer (+ source picker +
optional target + gates toggle); a **pipeline timeline** showing each
stage's status, artifact (SQL / spec / dataset link / metrics), and the
reviewer's verdict; the final report rendered like an analysis; every
produced dataset/model links into the catalog and Models rail.

## v2 phasing

| Phase | Contents |
|---|---|
| v2-P1 | Experiment store + background runner; Planning, Exploration, Cleaning, Programming, Code Review agents (through materialized clean dataset) |
| v2-P2 | Code-stage runtime (workdir contract, parquet in / figures+models+datasets out, allowlist review) + Visualization Agent; Feature Engineering, Model Algorithm (spec or code), Cross-Validation, Test, Metric Performance — full pipeline to report |
| v2-P3 | Human gates, rerun/compare experiments, scheduled re-evaluation workflows, experiment → Python project export |
