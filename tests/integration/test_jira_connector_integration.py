"""Integration tests for JiraConnector (real API, env-gated)."""

from __future__ import annotations

import os

import pytest

from genxai.connectors.jira import JiraConnector


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("JIRA_EMAIL")
    or not os.getenv("JIRA_API_TOKEN")
    or not os.getenv("JIRA_BASE_URL")
    or not os.getenv("JIRA_TEST_PROJECT_KEY"),
    reason="JIRA_EMAIL/JIRA_API_TOKEN/JIRA_BASE_URL/JIRA_TEST_PROJECT_KEY not set",
)
async def test_jira_connector_project_and_search() -> None:
    connector = JiraConnector(
        connector_id="jira_integration",
        email=os.environ["JIRA_EMAIL"],
        api_token=os.environ["JIRA_API_TOKEN"],
        base_url=os.environ["JIRA_BASE_URL"],
    )

    project_key = os.environ["JIRA_TEST_PROJECT_KEY"]

    await connector.start()
    project = await connector.get_project(project_key)
    search = await connector.search_issues(f"project={project_key}")
    await connector.stop()

    assert project.get("key")
    assert "issues" in search