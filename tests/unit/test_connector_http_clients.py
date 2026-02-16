"""Unit tests for HTTP-based connectors (Slack/GitHub/Notion/Jira/Google Workspace)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from enterprise.genxai.connectors.slack import SlackConnector
from enterprise.genxai.connectors.github import GitHubConnector
from enterprise.genxai.connectors.notion import NotionConnector
from enterprise.genxai.connectors.jira import JiraConnector
from enterprise.genxai.connectors.google_workspace import GoogleWorkspaceConnector


class FakeResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


class FakeClient:
    def __init__(self, responses: Dict[tuple[str, str], Dict[str, Any]]) -> None:
        self.responses = responses
        self.requests: list[Dict[str, Any]] = []
        self.closed = False

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> FakeResponse:
        self.requests.append({"method": "GET", "path": path, "params": params or {}})
        return FakeResponse(self.responses.get(("GET", path), {}))

    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> FakeResponse:
        self.requests.append(
            {"method": "POST", "path": path, "params": params or {}, "json": json or {}}
        )
        return FakeResponse(self.responses.get(("POST", path), {}))

    async def aclose(self) -> None:
        self.closed = True


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, module_path: str, client: FakeClient) -> None:
    monkeypatch.setattr(f"{module_path}.httpx.AsyncClient", lambda **_: client)


@pytest.mark.asyncio
async def test_slack_connector_send_message(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        ("POST", "/chat.postMessage"): {"ok": True, "ts": "123"},
        ("GET", "/conversations.list"): {"ok": True, "channels": []},
    }
    fake_client = FakeClient(responses)
    _patch_async_client(monkeypatch, "enterprise.genxai.connectors.slack", fake_client)

    connector = SlackConnector(connector_id="slack", bot_token="token")
    await connector.start()
    result = await connector.send_message(channel="#general", text="Hello")
    assert result["ok"] is True
    channels = await connector.list_channels()
    assert channels["ok"] is True

    events: list[Dict[str, Any]] = []

    async def handler(event):
        events.append(event.payload)

    connector.on_event(handler)
    await connector.handle_event({"type": "message"})
    assert events == [{"type": "message"}]


@pytest.mark.asyncio
async def test_github_connector_issue_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        ("GET", "/repos/genxai/genxai"): {"full_name": "genxai/genxai"},
        ("GET", "/repos/genxai/genxai/issues"): [{"id": 1}],
        ("POST", "/repos/genxai/genxai/issues"): {"id": 123},
    }
    fake_client = FakeClient(responses)
    _patch_async_client(monkeypatch, "enterprise.genxai.connectors.github", fake_client)

    connector = GitHubConnector(connector_id="github", token="token")
    await connector.start()
    repo = await connector.get_repo(owner="genxai", repo="genxai")
    assert repo["full_name"] == "genxai/genxai"
    issues = await connector.list_issues(owner="genxai", repo="genxai")
    assert issues[0]["id"] == 1
    created = await connector.create_issue(owner="genxai", repo="genxai", title="Test")
    assert created["id"] == 123


@pytest.mark.asyncio
async def test_notion_connector_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        ("GET", "/pages/page_1"): {"id": "page_1"},
        ("POST", "/databases/db_1/query"): {"results": []},
        ("POST", "/pages"): {"id": "page_2"},
    }
    fake_client = FakeClient(responses)
    _patch_async_client(monkeypatch, "enterprise.genxai.connectors.notion", fake_client)

    connector = NotionConnector(connector_id="notion", token="token")
    await connector.start()
    page = await connector.get_page("page_1")
    assert page["id"] == "page_1"
    result = await connector.query_database("db_1")
    assert result["results"] == []
    created = await connector.create_page({"parent": {"database_id": "db_1"}})
    assert created["id"] == "page_2"


@pytest.mark.asyncio
async def test_jira_connector_issue_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        ("GET", "/rest/api/3/project/OPS"): {"key": "OPS"},
        ("POST", "/rest/api/3/search"): {"issues": []},
        ("POST", "/rest/api/3/issue"): {"key": "OPS-1"},
    }
    fake_client = FakeClient(responses)
    _patch_async_client(monkeypatch, "enterprise.genxai.connectors.jira", fake_client)

    connector = JiraConnector(
        connector_id="jira",
        email="you@company.com",
        api_token="token",
        base_url="https://example.atlassian.net",
    )
    await connector.start()
    project = await connector.get_project("OPS")
    assert project["key"] == "OPS"
    search = await connector.search_issues("project=OPS")
    assert search["issues"] == []
    created = await connector.create_issue({"fields": {"summary": "Test"}})
    assert created["key"] == "OPS-1"


@pytest.mark.asyncio
async def test_google_workspace_connector(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = {
        ("GET", "/sheets/v4/spreadsheets/sheet_1"): {"spreadsheetId": "sheet_1"},
        ("POST", "/sheets/v4/spreadsheets/sheet_1/values/A1:append"): {"updates": {}},
        ("GET", "/drive/v3/files"): {"files": []},
        ("GET", "/calendar/v3/calendars/primary/events"): {"items": []},
    }
    fake_client = FakeClient(responses)
    _patch_async_client(monkeypatch, "enterprise.genxai.connectors.google_workspace", fake_client)

    connector = GoogleWorkspaceConnector(connector_id="gws", access_token="token")
    await connector.start()
    sheet = await connector.get_sheet("sheet_1")
    assert sheet["spreadsheetId"] == "sheet_1"
    append_result = await connector.append_sheet_values("sheet_1", "A1", [["Hello"]])
    assert "updates" in append_result
    files = await connector.list_drive_files()
    assert files["files"] == []
    events = await connector.get_calendar_events()
    assert events["items"] == []


@pytest.mark.asyncio
async def test_connector_validate_config_errors() -> None:
    with pytest.raises(ValueError):
        await SlackConnector(connector_id="slack", bot_token="").validate_config()
    with pytest.raises(ValueError):
        await GitHubConnector(connector_id="github", token="").validate_config()
    with pytest.raises(ValueError):
        await NotionConnector(connector_id="notion", token="").validate_config()
    with pytest.raises(ValueError):
        await JiraConnector(connector_id="jira", email="", api_token="token", base_url="url").validate_config()
    with pytest.raises(ValueError):
        await JiraConnector(connector_id="jira", email="a@b.com", api_token="", base_url="url").validate_config()
    with pytest.raises(ValueError):
        await JiraConnector(connector_id="jira", email="a@b.com", api_token="token", base_url="").validate_config()
    with pytest.raises(ValueError):
        await GoogleWorkspaceConnector(connector_id="gws", access_token="").validate_config()