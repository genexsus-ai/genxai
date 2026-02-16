"""Google Workspace connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging

import httpx

from .base import Connector

logger = logging.getLogger(__name__)


class GoogleWorkspaceConnector(Connector):
    """Google Workspace connector using Google REST APIs.

    Notes:
        - Provide an OAuth access token (Bearer) with required scopes.
        - Supports basic operations for Sheets, Drive, and Calendar.
    """

    def __init__(
        self,
        connector_id: str,
        access_token: str,
        name: Optional[str] = None,
        base_url: str = "https://www.googleapis.com",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _start(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )

    async def _stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_config(self) -> None:
        if not self.access_token:
            raise ValueError("Google Workspace access_token must be provided")

    async def get_sheet(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Fetch spreadsheet metadata."""
        return await self._get(f"/sheets/v4/spreadsheets/{spreadsheet_id}")

    async def append_sheet_values(
        self,
        spreadsheet_id: str,
        range_: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """Append values to a Google Sheet."""
        params = {"valueInputOption": value_input_option}
        payload = {"values": values}
        return await self._post(
            f"/sheets/v4/spreadsheets/{spreadsheet_id}/values/{range_}:append",
            payload,
            params=params,
        )

    async def list_drive_files(self, page_size: int = 10, query: Optional[str] = None) -> Dict[str, Any]:
        """List Drive files."""
        params: Dict[str, Any] = {"pageSize": page_size}
        if query:
            params["q"] = query
        return await self._get("/drive/v3/files", params=params)

    async def get_calendar_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """List calendar events."""
        params = {"maxResults": max_results, "singleEvents": True, "orderBy": "startTime"}
        return await self._get(f"/calendar/v3/calendars/{calendar_id}/events", params=params)

    async def handle_event(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """Handle an inbound event payload and emit it downstream."""
        await self.emit(payload=payload, metadata={"headers": headers or {}})

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    async def _post(
        self,
        path: str,
        payload: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.post(path, params=params or {}, json=payload)
        response.raise_for_status()
        return response.json()

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        async with self._lock:
            if self._client is None:
                await self._start()