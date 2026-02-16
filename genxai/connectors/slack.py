"""Slack connector implementation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio
import logging

import httpx

from .base import Connector

logger = logging.getLogger(__name__)


class SlackConnector(Connector):
    """Slack connector using Slack Web API + Events API payloads.

    Notes:
        - This connector handles outgoing API calls and can emit inbound events
          when `handle_event` is called by your webhook route.
        - You must provide a Slack Bot token for Web API calls.
    """

    def __init__(
        self,
        connector_id: str,
        bot_token: str,
        name: Optional[str] = None,
        base_url: str = "https://slack.com/api",
        timeout: float = 10.0,
    ) -> None:
        super().__init__(connector_id=connector_id, name=name)
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _start(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                timeout=self.timeout,
            )

    async def _stop(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def validate_config(self) -> None:
        if not self.bot_token:
            raise ValueError("Slack bot_token must be provided")

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel."""
        payload: Dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments
        return await self._post("/chat.postMessage", payload)

    async def post_ephemeral(
        self,
        channel: str,
        user: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send an ephemeral message to a user in a channel."""
        payload: Dict[str, Any] = {"channel": channel, "user": user, "text": text}
        if blocks:
            payload["blocks"] = blocks
        return await self._post("/chat.postEphemeral", payload)

    async def list_channels(self, types: str = "public_channel,private_channel") -> Dict[str, Any]:
        """List available channels."""
        return await self._get("/conversations.list", {"types": types})

    async def handle_event(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
        """Handle an inbound Slack event payload and emit it downstream."""
        await self.emit(payload=payload, metadata={"headers": headers or {}})

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        data = response.json()
        if not data.get("ok", False):
            raise ValueError(f"Slack API error: {data}")
        return data

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_client()
        assert self._client is not None
        response = await self._client.post(path, json=payload)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok", False):
            raise ValueError(f"Slack API error: {data}")
        return data

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        async with self._lock:
            if self._client is None:
                await self._start()