"""Integration tests for SlackConnector (real API, env-gated)."""

from __future__ import annotations

import os

import pytest

from genxai.connectors.slack import SlackConnector


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("SLACK_BOT_TOKEN") or not os.getenv("SLACK_TEST_CHANNEL"),
    reason="SLACK_BOT_TOKEN/SLACK_TEST_CHANNEL not set",
)
async def test_slack_connector_list_channels() -> None:
    connector = SlackConnector(
        connector_id="slack_integration",
        bot_token=os.environ["SLACK_BOT_TOKEN"],
    )

    await connector.start()
    channels = await connector.list_channels()
    await connector.stop()

    assert channels.get("ok") is True


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("SLACK_BOT_TOKEN") or not os.getenv("SLACK_TEST_CHANNEL"),
    reason="SLACK_BOT_TOKEN/SLACK_TEST_CHANNEL not set",
)
async def test_slack_connector_send_message() -> None:
    connector = SlackConnector(
        connector_id="slack_integration",
        bot_token=os.environ["SLACK_BOT_TOKEN"],
    )

    await connector.start()
    response = await connector.send_message(
        channel=os.environ["SLACK_TEST_CHANNEL"],
        text="GenXAI connector integration test",
    )
    await connector.stop()

    assert response.get("ok") is True