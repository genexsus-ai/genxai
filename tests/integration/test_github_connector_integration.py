"""Integration tests for GitHubConnector (real API, env-gated)."""

from __future__ import annotations

import os

import pytest

from genxai.connectors.github import GitHubConnector


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN")
    or not os.getenv("GITHUB_TEST_OWNER")
    or not os.getenv("GITHUB_TEST_REPO"),
    reason="GITHUB_TOKEN/GITHUB_TEST_OWNER/GITHUB_TEST_REPO not set",
)
async def test_github_connector_repo_and_issues() -> None:
    connector = GitHubConnector(
        connector_id="github_integration",
        token=os.environ["GITHUB_TOKEN"],
    )

    owner = os.environ["GITHUB_TEST_OWNER"]
    repo = os.environ["GITHUB_TEST_REPO"]

    await connector.start()
    repo_info = await connector.get_repo(owner=owner, repo=repo)
    issues = await connector.list_issues(owner=owner, repo=repo, per_page=5)
    await connector.stop()

    assert repo_info.get("full_name")
    assert isinstance(issues, list)