"""Integration tests for GoogleWorkspaceConnector (real API, env-gated)."""

from __future__ import annotations

import os

import pytest

from genxai.connectors.google_workspace import GoogleWorkspaceConnector


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GWS_ACCESS_TOKEN") or not os.getenv("GWS_TEST_SHEET_ID"),
    reason="GWS_ACCESS_TOKEN/GWS_TEST_SHEET_ID not set",
)
async def test_google_workspace_connector_sheet_and_drive() -> None:
    connector = GoogleWorkspaceConnector(
        connector_id="gws_integration",
        access_token=os.environ["GWS_ACCESS_TOKEN"],
    )

    sheet_id = os.environ["GWS_TEST_SHEET_ID"]

    await connector.start()
    sheet = await connector.get_sheet(sheet_id)
    files = await connector.list_drive_files(page_size=5)
    events = await connector.get_calendar_events(max_results=5)
    await connector.stop()

    assert sheet.get("spreadsheetId")
    assert "files" in files
    assert "items" in events