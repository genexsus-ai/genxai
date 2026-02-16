"""Webhook trigger implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional
import hmac
import hashlib
import logging

from enterprise.genxai.triggers.base import BaseTrigger

logger = logging.getLogger(__name__)


class WebhookTrigger(BaseTrigger):
    """HTTP webhook trigger.

    This trigger does not start its own web server; it provides a handler that
    can be mounted in FastAPI or other ASGI frameworks.
    """

    def __init__(
        self,
        trigger_id: str,
        secret: Optional[str] = None,
        name: Optional[str] = None,
        header_name: str = "X-GenXAI-Signature",
        hash_alg: str = "sha256",
    ) -> None:
        super().__init__(trigger_id=trigger_id, name=name)
        self.secret = secret
        self.header_name = header_name
        self.hash_alg = hash_alg

    async def _start(self) -> None:
        logger.debug("Webhook trigger %s ready for requests", self.trigger_id)

    async def _stop(self) -> None:
        logger.debug("Webhook trigger %s stopped", self.trigger_id)

    def validate_signature(self, payload: bytes, signature: Optional[str]) -> bool:
        """Validate the webhook signature when a secret is provided."""
        if not self.secret:
            return True
        if not signature:
            return False

        digest = hmac.new(self.secret.encode(), payload, getattr(hashlib, self.hash_alg)).hexdigest()
        expected = f"{self.hash_alg}={digest}"
        return hmac.compare_digest(expected, signature)

    async def handle_request(
        self,
        payload: Dict[str, Any],
        raw_body: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Process an inbound webhook request and emit a trigger event."""
        headers = headers or {}
        signature = headers.get(self.header_name)

        if self.secret and raw_body is not None:
            if not self.validate_signature(raw_body, signature):
                logger.warning("Webhook signature validation failed for %s", self.trigger_id)
                return {"status": "rejected", "reason": "invalid signature"}

        await self.emit(payload=payload, metadata={"headers": headers})
        return {"status": "accepted", "trigger_id": self.trigger_id}