"""In-memory run store for GenXBot prototype."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from app.schemas import RunSession


class RunStore:
    """Simple in-memory store for run sessions."""

    def __init__(self) -> None:
        self._runs: dict[str, RunSession] = {}

    def create(self, run: RunSession) -> RunSession:
        self._runs[run.id] = run
        return run

    def get(self, run_id: str) -> Optional[RunSession]:
        return self._runs.get(run_id)

    def update(self, run: RunSession) -> RunSession:
        self._runs[run.id] = run
        return run

    def list_runs(self) -> Iterable[RunSession]:
        return self._runs.values()
