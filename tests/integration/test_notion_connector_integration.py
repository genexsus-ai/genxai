"""Integration tests for NotionConnector (real API, env-gated)."""

from __future__ import annotations

import os

import pytest

from genxai.connectors.notion import NotionConnector


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("NOTION_TOKEN")
    or not os.getenv("NOTION_TEST_PAGE_ID")
    or not os.getenv("NOTION_TEST_DB_ID"),
    reason="NOTION_TOKEN/NOTION_TEST_PAGE_ID/NOTION_TEST_DB_ID not set",
)
async def test_notion_connector_page_and_db_query() -> None:
    connector = NotionConnector(
        connector_id="notion_integration",
        token=os.environ["NOTION_TOKEN"],
    )

    page_id = os.environ["NOTION_TEST_PAGE_ID"]
    db_id = os.environ["NOTION_TEST_DB_ID"]

    await connector.start()
    page = await connector.get_page(page_id)
    db_results = await connector.query_database(db_id)
    await connector.stop()

    assert page.get("id")
    assert "results" in db_results