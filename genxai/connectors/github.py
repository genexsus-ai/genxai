"""GitHub connector implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging

import httpx

from .base import Connector

logger = logging.getLogger(__name__)


class GitHubConnector(Connector):
    """GitHub connector using REST API v3.

    Notes:
        - Provide a personal access token with required scopes.
        - Incoming webhook events can be forwarded to `handle_event`.
    """

    def __init__(
        self,
        connector_id: str,
        token: str,
        name: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _start(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=self.timeout,
            )

    async def _stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_config(self) -> None:
        if not self.token:
            raise ValueError("GitHub token must be provided")

    async def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository metadata."""
        return await self._get(f"/repos/{owner}/{repo}")

    async def list_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 30,
    ) -> Any:
        """List issues for a repository."""
        return await self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page},
        )

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new GitHub issue."""
        payload: Dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        return await self._post(f"/repos/{owner}/{repo}/issues", payload)

    async def handle_event(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Handle an inbound GitHub webhook event and emit it downstream."""
        await self.emit(payload=payload, metadata={"headers": headers or {}})

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
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