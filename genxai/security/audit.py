"""Audit logging and approvals for governance."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import sqlite3


@dataclass
class AuditEvent:
    action: str
    actor_id: str
    resource_id: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    resource_id: str
    actor_id: str
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditStore:
    """SQLite-backed store for audit logs and approvals."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _with_connection(self, handler):
        conn = self._connect()
        try:
            return handler(conn)
        finally:
            conn.close()

    def _ensure_db(self) -> None:
        def _init(conn: sqlite3.Connection) -> None:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

        self._with_connection(_init)

    def load_events(self) -> List[AuditEvent]:
        def _load(conn: sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT action, actor_id, resource_id, status, metadata, timestamp FROM audit_events"
            )
            return cursor.fetchall()

        rows = self._with_connection(_load)
        events: List[AuditEvent] = []
        for action, actor_id, resource_id, status, metadata, timestamp in rows:
            events.append(
                AuditEvent(
                    action=action,
                    actor_id=actor_id,
                    resource_id=resource_id,
                    status=status,
                    metadata=json.loads(metadata),
                    timestamp=datetime.fromisoformat(timestamp),
                )
            )
        return events

    def save_event(self, event: AuditEvent) -> None:
        def _save(conn: sqlite3.Connection) -> None:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_events (action, actor_id, resource_id, status, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.action,
                    event.actor_id,
                    event.resource_id,
                    event.status,
                    json.dumps(event.metadata, default=str),
                    event.timestamp.isoformat(),
                ),
            )
            conn.commit()

        self._with_connection(_save)

    def clear_events(self) -> None:
        def _clear(conn: sqlite3.Connection) -> None:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audit_events")
            conn.commit()

        self._with_connection(_clear)

    def load_requests(self) -> Dict[str, ApprovalRequest]:
        def _load(conn: sqlite3.Connection):
            cursor = conn.cursor()
            cursor.execute(
                "SELECT request_id, action, resource_id, actor_id, status, created_at FROM approval_requests"
            )
            return cursor.fetchall()

        rows = self._with_connection(_load)
        requests: Dict[str, ApprovalRequest] = {}
        for request_id, action, resource_id, actor_id, status, created_at in rows:
            requests[request_id] = ApprovalRequest(
                request_id=request_id,
                action=action,
                resource_id=resource_id,
                actor_id=actor_id,
                status=status,
                created_at=datetime.fromisoformat(created_at),
            )
        return requests

    def save_request(self, request: ApprovalRequest) -> None:
        def _save(conn: sqlite3.Connection) -> None:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO approval_requests
                (request_id, action, resource_id, actor_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.action,
                    request.resource_id,
                    request.actor_id,
                    request.status,
                    request.created_at.isoformat(),
                ),
            )
            conn.commit()

        self._with_connection(_save)

    def clear_requests(self) -> None:
        def _clear(conn: sqlite3.Connection) -> None:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM approval_requests")
            conn.commit()

        self._with_connection(_clear)

    def vacuum(self) -> None:
        def _vacuum(conn: sqlite3.Connection) -> None:
            conn.execute("VACUUM")

        self._with_connection(_vacuum)


class AuditLog:
    """In-memory audit log."""

    def __init__(self) -> None:
        self._store = _get_audit_store()
        self._events: List[AuditEvent] = self._store.load_events()

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)
        self._store.save_event(event)

    def list_events(self) -> List[AuditEvent]:
        self._events = self._store.load_events()
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._store.clear_events()


class ApprovalService:
    """Simple in-memory approval workflow."""

    def __init__(self) -> None:
        self._store = _get_audit_store()
        self._requests: Dict[str, ApprovalRequest] = self._store.load_requests()
        self._counter = self._infer_counter()

    def _infer_counter(self) -> int:
        max_counter = 0
        for request_id in self._requests:
            if request_id.startswith("approval_"):
                try:
                    max_counter = max(max_counter, int(request_id.split("_", 1)[1]))
                except ValueError:
                    continue
        return max_counter

    def submit(self, action: str, resource_id: str, actor_id: str) -> ApprovalRequest:
        self._counter += 1
        request_id = f"approval_{self._counter}"
        request = ApprovalRequest(
            request_id=request_id,
            action=action,
            resource_id=resource_id,
            actor_id=actor_id,
        )
        self._requests[request_id] = request
        self._store.save_request(request)
        return request

    def approve(self, request_id: str) -> Optional[ApprovalRequest]:
        request = self._requests.get(request_id)
        if request:
            request.status = "approved"
            self._store.save_request(request)
        return request

    def reject(self, request_id: str) -> Optional[ApprovalRequest]:
        request = self._requests.get(request_id)
        if request:
            request.status = "rejected"
            self._store.save_request(request)
        return request

    def get(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def clear(self) -> None:
        self._requests.clear()
        self._counter = 0
        self._store.clear_requests()


_audit_log: Optional[AuditLog] = None
_approval_service: Optional[ApprovalService] = None
_audit_store: Optional[AuditStore] = None


def _get_default_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "audit.db"


def _get_audit_store() -> AuditStore:
    global _audit_store
    if _audit_store is None:
        db_path = Path(os.getenv("GENXAI_AUDIT_DB", str(_get_default_db_path())))
        _audit_store = AuditStore(db_path)
    return _audit_store


def get_audit_log() -> AuditLog:
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


def get_approval_service() -> ApprovalService:
    global _approval_service
    if _approval_service is None:
        _approval_service = ApprovalService()
    return _approval_service


def reset_audit_services() -> None:
    """Reset audit services (useful for tests)."""
    global _audit_log, _approval_service, _audit_store
    _audit_log = None
    _approval_service = None
    _audit_store = None


def _alias_enterprise_module() -> None:
    """Ensure enterprise.* imports resolve to this module instance.

    Some test shims create a synthetic `enterprise.genxai` package that points
    to the local source tree. Without aliasing, imports like
    `enterprise.genxai.security.audit` can create a second module instance,
    leading to duplicated singleton state. We alias to keep a single state.
    """

    module_name = __name__
    alias_name = "enterprise.genxai.security.audit"
    sys.modules[alias_name] = sys.modules[module_name]


_alias_enterprise_module()