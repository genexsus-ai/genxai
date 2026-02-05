"""Execution metadata store for workflow runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import json
import uuid


@dataclass
class ExecutionRecord:
    """Represents a workflow execution record."""

    run_id: str
    workflow: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workflow": self.workflow,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "error": self.error,
            "result": self.result,
        }


class ExecutionStore:
    """Execution store with JSON or SQL persistence support."""

    def __init__(
        self,
        persistence_path: Optional[Path] = None,
        sql_url: Optional[str] = None,
    ) -> None:
        self._records: Dict[str, ExecutionRecord] = {}
        self._persistence_path = persistence_path
        self._sql_url = sql_url
        self._engine = None
        self._table = None

        if sql_url:
            try:
                import sqlalchemy as sa
            except Exception as exc:
                raise ImportError(
                    "sqlalchemy is required for SQL persistence. Install with: pip install sqlalchemy"
                ) from exc
            self._engine = sa.create_engine(sql_url)
            metadata = sa.MetaData()
            self._table = sa.Table(
                "genxai_executions",
                metadata,
                sa.Column("run_id", sa.String, primary_key=True),
                sa.Column("workflow", sa.String, nullable=False),
                sa.Column("status", sa.String, nullable=False),
                sa.Column("started_at", sa.String, nullable=False),
                sa.Column("completed_at", sa.String),
                sa.Column("metadata", sa.JSON, nullable=True),
                sa.Column("error", sa.Text, nullable=True),
                sa.Column("result", sa.JSON, nullable=True),
            )
            metadata.create_all(self._engine)

    def generate_run_id(self) -> str:
        return str(uuid.uuid4())

    def create(
        self,
        run_id: str,
        workflow: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionRecord:
        if run_id in self._records:
            return self._records[run_id]

        record = ExecutionRecord(
            run_id=run_id,
            workflow=workflow,
            status=status,
            started_at=datetime.now().isoformat(),
            metadata=metadata or {},
        )
        self._records[run_id] = record
        self._persist(record)
        return record

    def update(
        self,
        run_id: str,
        status: Optional[str] = None,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        completed: bool = False,
    ) -> ExecutionRecord:
        record = self._records.get(run_id)
        if record is None:
            record = self.create(run_id, workflow="unknown", status="unknown")
        if status is not None:
            record.status = status
        if error is not None:
            record.error = error
        if result is not None:
            record.result = result
        if metadata:
            record.metadata.update(metadata)
        if completed:
            record.completed_at = datetime.now().isoformat()
        self._persist(record)
        return record

    def get(self, run_id: str) -> Optional[ExecutionRecord]:
        record = self._records.get(run_id)
        if record or not self._engine or not self._table:
            return record

        import sqlalchemy as sa

        with self._engine.begin() as conn:
            stmt = sa.select(self._table).where(self._table.c.run_id == run_id)
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            record = ExecutionRecord(
                run_id=row["run_id"],
                workflow=row["workflow"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                metadata=row["metadata"] or {},
                error=row["error"],
                result=row["result"],
            )
            self._records[run_id] = record
            return record

    def _persist(self, record: ExecutionRecord) -> None:
        if self._engine is not None and self._table is not None:
            import sqlalchemy as sa

            payload = record.to_dict()
            with self._engine.begin() as conn:
                stmt = sa.select(self._table.c.run_id).where(
                    self._table.c.run_id == record.run_id
                )
                exists = conn.execute(stmt).first()
                if exists:
                    conn.execute(
                        self._table.update()
                        .where(self._table.c.run_id == record.run_id)
                        .values(**payload)
                    )
                else:
                    conn.execute(self._table.insert().values(**payload))

        if not self._persistence_path:
            return
        self._persistence_path.mkdir(parents=True, exist_ok=True)
        path = self._persistence_path / f"execution_{record.run_id}.json"
        path.write_text(json.dumps(record.to_dict(), indent=2, default=str))

    def close(self) -> None:
        """Dispose of SQL resources if enabled."""
        if self._engine is not None:
            self._engine.dispose()

    def __del__(self) -> None:
        self.close()