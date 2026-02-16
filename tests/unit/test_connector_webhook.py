"""Unit tests for webhook connector."""

import hmac
import hashlib
import pytest

from enterprise.genxai.connectors.webhook import WebhookConnector


@pytest.mark.asyncio
async def test_webhook_connector_signature_validation():
    connector = WebhookConnector(connector_id="webhook", secret="secret")
    payload = {"hello": "world"}
    raw = b"{\"hello\": \"world\"}"

    digest = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"

    response = await connector.handle_request(
        payload=payload,
        raw_body=raw,
        headers={"X-GenXAI-Signature": signature},
    )

    assert response["status"] == "accepted"

    rejected = await connector.handle_request(
        payload=payload,
        raw_body=raw,
        headers={"X-GenXAI-Signature": "sha256=bad"},
    )

    assert rejected["status"] == "rejected"


@pytest.mark.asyncio
async def test_webhook_connector_validate_config_rejects_invalid_hash():
    connector = WebhookConnector(connector_id="webhook", secret="secret", hash_alg="bad")
    with pytest.raises(ValueError):
        await connector.validate_config()