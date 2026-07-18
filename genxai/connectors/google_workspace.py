"""Google Workspace connector implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

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
        name: str | None = None,
        base_url: str = "https://www.googleapis.com",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
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

    async def get_sheet(self, spreadsheet_id: str) -> dict[str, Any]:
        """Fetch spreadsheet metadata."""
        return await self._get(f"/sheets/v4/spreadsheets/{spreadsheet_id}")

    async def get_sheet_values(
        self, spreadsheet_id: str, range_: str
    ) -> dict[str, Any]:
        """Read cell values from a Google Sheet (unformatted, typed)."""
        return await self._get(
            f"/sheets/v4/spreadsheets/{spreadsheet_id}/values/{range_}",
            params={"valueRenderOption": "UNFORMATTED_VALUE"},
        )

    async def append_sheet_values(
        self,
        spreadsheet_id: str,
        range_: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Append values to a Google Sheet."""
        params = {"valueInputOption": value_input_option}
        payload = {"values": values}
        return await self._post(
            f"/sheets/v4/spreadsheets/{spreadsheet_id}/values/{range_}:append",
            payload,
            params=params,
        )

    async def update_sheet_values(
        self,
        spreadsheet_id: str,
        range_: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Overwrite cell values in a Google Sheet range."""
        params = {"valueInputOption": value_input_option}
        payload = {"values": values}
        return await self._put(
            f"/sheets/v4/spreadsheets/{spreadsheet_id}/values/{range_}",
            payload,
            params=params,
        )

    async def upsert_sheet_row(
        self,
        spreadsheet_id: str,
        sheet: str,
        key_column: str,
        key_value: Any,
        values: list[Any],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """Append or update a row matched by a key column (n8n-style upsert).

        ``key_column`` is a header name from row 1 (e.g. "Email") or a column
        letter ("C"). Rows 2+ are scanned for ``key_value``; a match updates
        that row in place, otherwise ``values`` is appended as a new row.
        """
        # Accept a single row passed as [[...]] too
        if len(values) == 1 and isinstance(values[0], list):
            values = values[0]

        data = await self.get_sheet_values(spreadsheet_id, sheet)
        rows: list[list[Any]] = data.get("values") or []

        column = key_column.strip()
        if len(column) <= 2 and column.upper() == column and column.isalpha():
            index = sum(
                (ord(ch) - ord("A") + 1) * 26**i
                for i, ch in enumerate(reversed(column.upper()))
            ) - 1
        else:
            header = rows[0] if rows else []
            if column not in header:
                raise ValueError(
                    f"Key column {column!r} not found in header row: {header!r}"
                )
            index = header.index(column)

        match_row = next(
            (
                i + 1  # 1-based sheet row number
                for i, row in enumerate(rows)
                if i > 0 and index < len(row) and str(row[index]) == str(key_value)
            ),
            None,
        )
        if match_row is not None:
            response = await self.update_sheet_values(
                spreadsheet_id,
                f"{sheet}!A{match_row}",
                [values],
                value_input_option=value_input_option,
            )
            return {"action": "updated", "row": match_row, **response}
        response = await self.append_sheet_values(
            spreadsheet_id, f"{sheet}!A1", [values], value_input_option=value_input_option
        )
        return {"action": "appended", **response}

    async def list_drive_files(self, page_size: int = 10, query: str | None = None) -> dict[str, Any]:
        """List Drive files."""
        params: dict[str, Any] = {"pageSize": page_size}
        if query:
            params["q"] = query
        return await self._get("/drive/v3/files", params=params)

    async def get_calendar_events(
        self,
        calendar_id: str = "primary",
        max_results: int = 10,
    ) -> dict[str, Any]:
        """List calendar events."""
        params = {"maxResults": max_results, "singleEvents": True, "orderBy": "startTime"}
        return await self._get(f"/calendar/v3/calendars/{calendar_id}/events", params=params)

    async def create_calendar_event(
        self,
        summary: str,
        start: str,
        end: str | None = None,
        calendar_id: str = "primary",
        description: str | None = None,
        attendees: list[str] | str | None = None,
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Create a calendar event (e.g. schedule a follow-up).

        ``start``/``end`` are RFC3339 datetimes ("2026-07-16T15:00:00");
        ``end`` defaults to 30 minutes after ``start``. ``attendees`` takes a
        list of emails or one comma-separated string. Needs the
        calendar.events OAuth scope.
        """
        from datetime import datetime, timedelta

        if end is None:
            parsed = datetime.fromisoformat(start)
            end = (parsed + timedelta(minutes=30)).isoformat()
        payload: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        if description:
            payload["description"] = description
        if attendees:
            emails = (
                [email.strip() for email in attendees.split(",") if email.strip()]
                if isinstance(attendees, str)
                else attendees
            )
            payload["attendees"] = [{"email": email} for email in emails]
        return await self._post(
            f"/calendar/v3/calendars/{calendar_id}/events", payload
        )

    async def handle_event(self, payload: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        """Handle an inbound event payload and emit it downstream."""
        await self.emit(payload=payload, metadata={"headers": headers or {}})

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    async def _post(
        self,
        path: str,
        payload: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.post(path, params=params or {}, json=payload)
        response.raise_for_status()
        return response.json()

    async def _put(
        self,
        path: str,
        payload: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.put(path, params=params or {}, json=payload)
        response.raise_for_status()
        return response.json()

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        async with self._lock:
            if self._client is None:
                await self._start()
