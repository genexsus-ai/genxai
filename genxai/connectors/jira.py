"""Jira connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import base64
import logging

import httpx

from .base import Connector

logger = logging.getLogger(__name__)


class JiraConnector(Connector):
    """Jira connector using Jira Cloud REST API v3.

    Notes:
        - Use email + API token for basic auth.
        - Incoming webhook events can be forwarded to `handle_event`.
    """

    def __init__(
        self,
        connector_id: str,
        email: str,
        api_token: str,
        base_url: str,
        name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.email = email
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _start(self) -> None:
        if not self._client:
            token = f"{self.email}:{self.api_token}".encode("utf-8")
            auth_header = base64.b64encode(token).decode("utf-8")
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Basic {auth_header}",
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
        if not self.email:
            raise ValueError("Jira email must be provided")
        if not self.api_token:
            raise ValueError("Jira api_token must be provided")
        if not self.base_url:
            raise ValueError("Jira base_url must be provided")

    async def get_project(self, project_key: str) -> Dict[str, Any]:
        """Fetch Jira project metadata."""
        return await self._get(f"/rest/api/3/project/{project_key}")

    async def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Search issues with JQL."""
        payload = {"jql": jql, "maxResults": max_results}
        return await self._post("/rest/api/3/search", payload)

    async def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Jira issue using the provided payload."""
        return await self._post("/rest/api/3/issue", payload)

    async def handle_event(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
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