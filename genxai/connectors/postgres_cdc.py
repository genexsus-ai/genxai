"""Postgres CDC connector implementation (wal2json)."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import json
import logging


from .base import Connector

logger = logging.getLogger(__name__)


class PostgresCDCConnector(Connector):
    """Postgres CDC connector using wal2json output plugin."""

    def __init__(
        self,
        connector_id: str,
        dsn: str,
        slot_name: str,
        publication: str,
        name: Optional[str] = None,
        poll_interval: float = 1.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.dsn = dsn
        self.slot_name = slot_name
        self.publication = publication
        self.poll_interval = poll_interval
        self._conn: Optional[Any] = None
        self._task: Optional[asyncio.Task[None]] = None

    async def _start(self) -> None:
        import asyncpg

        self._conn = await asyncpg.connect(self.dsn)
        await self._ensure_slot()
        self._task = asyncio.create_task(self._consume_loop())

    async def _stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def validate_config(self) -> None:
        if not self.dsn:
            raise ValueError("Postgres CDC dsn must be provided")
        if not self.slot_name:
            raise ValueError("Postgres CDC slot_name must be provided")
        if not self.publication:
            raise ValueError("Postgres CDC publication must be provided")

    async def _ensure_slot(self) -> None:
        assert self._conn is not None
        await self._conn.execute(
            "SELECT * FROM pg_create_logical_replication_slot($1, 'wal2json') "
            "ON CONFLICT DO NOTHING;",
            self.slot_name,
        )

    async def _consume_loop(self) -> None:
        while True:
            try:
                assert self._conn is not None
                rows = await self._conn.fetch(
                    "SELECT data FROM pg_logical_slot_get_changes($1, NULL, NULL, 'pretty-print', '1')",
                    self.slot_name,
                )
                for row in rows:
                    payload = self._deserialize(row["data"])
                    await self.emit(payload=payload)
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Postgres CDC error: %s", exc)
                await asyncio.sleep(self.poll_interval)

    def _deserialize(self, raw: Optional[str]) -> Any:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw

    async def handle_change(self, payload: Dict[str, Any]) -> None:
        await self.emit(payload=payload)