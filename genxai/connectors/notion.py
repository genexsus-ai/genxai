"""Notion connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging

import httpx

from .base import Connector

logger = logging.getLogger(__name__)


class NotionConnector(Connector):
    """Notion connector using the Notion API.

    Notes:
        - Provide a Notion integration token.
        - Incoming webhook-like events can be forwarded to `handle_event`.
    """

    def __init__(
        self,
        connector_id: str,
        token: str,
        name: Optional[str] = None,
        base_url: str = "https://api.notion.com/v1",
        notion_version: str = "2022-06-28",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.notion_version = notion_version
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _start(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Notion-Version": self.notion_version,
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )

    async def _stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_config(self) -> None:
        if not self.token:
            raise ValueError("Notion token must be provided")

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Fetch a Notion page by ID."""
        return await self._get(f"/pages/{page_id}")

    async def query_database(self, database_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query a Notion database."""
        return await self._post(f"/databases/{database_id}/query", payload or {})

    async def create_page(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Notion page using the provided payload."""
        return await self._post("/pages", payload)

    async def handle_event(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """Handle an inbound Notion event payload and emit it downstream."""
        await self.emit(payload=payload, metadata={"headers": headers or {}})

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.post(path, json=payload)
        response.raise_for_status()
        return response.json()

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        async with self._lock:
            if self._client is None:
                await self._start()