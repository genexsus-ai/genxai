"""In-memory repository implementation."""

import uuid

from app.application.services.brainstorm_service import StrategyRepository


class InMemoryStrategyRepository(StrategyRepository):
    """Simple in-memory repository for sessions."""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, session: dict) -> None:
        session_id = session.get("id") or str(uuid.uuid4())
        session["id"] = session_id
        self._store[session_id] = session

    def get(self, session_id: str) -> dict | None:
        return self._store.get(session_id)