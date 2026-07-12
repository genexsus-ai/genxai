# Data Science App — Design

Status: **fully implemented** (P1-P3: agent loop, charts, rerun-all, cell->dataset, scheduled reports, ML primitives)
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
