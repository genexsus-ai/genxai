# Analytics Data Sources — Design

Status: **proposed**
Scope: Analytics app reads from relational databases, Excel/CSV files, and
internal datasets through one abstraction — not just the internal SQLite
dataset store.

## Problem

The Analytics app currently reads exactly one backend: the internal
`DatasetStore` (SQLite), populated by `dataset_write` nodes. Real analytics
questions live in data that already exists elsewhere — a Postgres table, an
Excel export, a CSV somebody emails around. Today the only path is to build
a workflow that copies that data into a dataset first. That's the right
*option* (see "Two modes" below) but the wrong *requirement*.

## Two modes, both legitimate

1. **Ingest (already works):** a workflow extracts (Postgres `query`,
   `excel_read`, `file_download`) and lands rows in a dataset via
   `dataset_write`. Right when data needs history, transformation, or
   agent processing on the way in. This design does not change it.
2. **Connect (this design):** point Analytics directly at where data lives
   and explore it read-only, no copy. Right for "just show me the table."

## Core abstraction: Data Sources

A **source** is a named, registered pointer to tabular data. One registry,
three kinds at first:

```json
{"id": "…", "name": "Orders (prod)",  "kind": "sql",
 "config": {"credential": "warehouse", "table": "orders"}}

{"id": "…", "name": "Q2 spreadsheet", "kind": "file",
 "config": {"file_id": "<sha256>", "sheet": "Sales", "format": "xlsx"}}

{"id": "…", "name": "news_articles",  "kind": "dataset",
 "config": {"dataset": "news_articles"}}   // auto-registered, not stored
```

Registry persists in the existing `datasets.db` (a `sources` table).
Internal datasets are **implicit sources** — they all appear automatically,
so the current UX regresses nowhere.

### Adapter interface

Every kind implements the same three operations the Analytics UI already
consumes (the UI keeps its table, chart builder, and Ask AI unchanged —
they just target `/analytics/sources/{id}/…` instead of `/datasets/{name}/…`):

```python
class SourceAdapter(Protocol):
    def schema(self) -> list[{"name", "type"}]          # inferred columns
    def rows(self, limit, offset) -> {"rows", "total"}   # newest/natural order
    def aggregate(self, metric, field, group_by) -> [{"group", "value", "rows"}]
```

- **DatasetAdapter** — wraps the existing `DatasetStore` calls. Zero new logic.
- **SQLAdapter** — SQLAlchemy engine from a **credential in the existing
  encrypted store** (same credentials the Postgres connector uses — one
  "warehouse" credential serves workflows *and* analytics). `rows` pages
  with LIMIT/OFFSET; `aggregate` is **pushed down** as
  `SELECT group, AGG(field) FROM table GROUP BY group` so a million-row
  table aggregates in the database, not in Python. Identifier-validated,
  SELECT-only, row-capped — same safety model as the connector.
- **FileAdapter** — resolves a file-store ref; parses `.xlsx` via the
  `excel_read` machinery or `.csv` via stdlib; caps at ~50k rows; caches the
  parsed frame in memory keyed by content hash (content-addressing makes
  invalidation free — new file = new id).

### Upload path (files)

Files currently enter the store only through tools. Analytics needs a
browser path: `POST /api/v1/files/upload` (multipart) → saves to the file
store → returns the ref → UI immediately offers "register as source"
(with sheet picker for workbooks).

## API

```
GET    /analytics/sources                      # all sources incl. implicit datasets
POST   /analytics/sources                      # register sql/file source
DELETE /analytics/sources/{id}
GET    /analytics/sources/{id}/schema
GET    /analytics/sources/{id}/rows?limit&offset
GET    /analytics/sources/{id}/aggregate?metric&field&group_by
POST   /analytics/sources/{id}/analyze         # Ask AI (generalized from datasets)
POST   /files/upload                           # multipart -> file ref
```

Existing `/datasets/*` endpoints stay (used by tools/tests); the UI moves to
the sources endpoints.

## Frontend

`DatasetsView` generalizes to a **Sources** explorer:

- Sidebar list grouped by kind: 🗄 Datasets (implicit), 🐘 Databases,
  📄 Files — same selection model as today.
- **"+ Add source"** dialog:
  - *Database table*: credential picker (existing credentials of type
    postgres) → `list_tables` populates a table dropdown → name it.
  - *Upload file*: file input → upload → sheet picker (xlsx) → name it.
- Detail pane is unchanged: paged table, chart builder (group-by ×
  measure), Ask AI. They already operate on `{rows, total}` /
  `{group, value}` shapes, which is exactly what adapters return.

## Security

- SQL sources: reuse encrypted write-only credentials; adapters run
  SELECT-only with bound parameters and identifier validation; a source
  config never contains a password.
- File sources: refs into the local file store only.
- Analyze: samples the newest N rows exactly like today; same key handling.

## Performance notes

- SQL pushdown makes DB sources the *fastest* kind, not the slowest.
- File adapter is memory-bound by design (50k-row cap, surfaced in the UI
  as a truncation notice).
- **Future engine upgrade (P3+): DuckDB.** One embedded dependency would
  query CSV/Excel/Parquet files directly, federate across sources, and do
  window functions — the natural growth path when the chart builder
  outgrows single-table GROUP BY. The adapter interface is deliberately
  small so DuckDB can slot in behind it without UI changes.

## Phasing

| Phase | Contents |
|---|---|
| P1 | Source registry + DatasetAdapter + SQLAdapter (credential + table), sources endpoints, UI: grouped list + Add-database-source dialog |
| P2 | Upload endpoint + FileAdapter (xlsx/csv, sheet picker), Ask AI over any source |
| P3 | Custom-SQL sources (read-only), scheduled materialization ("sync this source into a dataset hourly" — generates a workflow), DuckDB engine option, Google Sheets kind |

## Non-goals (for now)

- Cross-source joins (DuckDB territory, P3+).
- Write-back from Analytics (Analytics stays read-only; writes are
  workflows' job).
- Multi-user source permissions (single-tenant studio today).
