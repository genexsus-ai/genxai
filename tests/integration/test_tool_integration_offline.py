"""Offline integration tests for built-in tools using local fixtures/mocks."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict

import pytest

from genxai.tools.builtin.file.file_reader import FileReaderTool
from genxai.tools.builtin.file.file_writer import FileWriterTool
from genxai.tools.builtin.file.directory_scanner import DirectoryScannerTool
from genxai.tools.builtin.database.sql_query import SQLQueryTool
from genxai.tools.builtin.database.database_inspector import DatabaseInspectorTool
from genxai.tools.builtin.web.api_caller import APICallerTool
from genxai.tools.builtin.web.http_client import HTTPClientTool


class DummyElapsed:
    def total_seconds(self) -> float:
        return 0.001


class DummyResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] | None = None,
        text: str = "ok",
        headers: Dict[str, str] | None = None,
        url: str = "https://example.com",
        history: list | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {"ok": True}
        self.text = text
        self.headers = headers or {"content-type": "application/json"}
        self.url = url
        self.reason_phrase = "OK"
        self.http_version = "HTTP/1.1"
        self.cookies = {}
        self.history = history or []
        self.content = text.encode("utf-8")
        self.elapsed = DummyElapsed()

    def json(self) -> Dict[str, Any]:
        return self._json_data


class DummyAsyncClient:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def request(self, method: str, url: str, **kwargs: Any) -> DummyResponse:
        return DummyResponse(json_data={"method": method, "url": url})


@pytest.mark.integration
@pytest.mark.asyncio
async def test_file_tools_round_trip(tmp_path: Path) -> None:
    """Write then read a file using file tools."""
    writer = FileWriterTool()
    reader = FileReaderTool()
    scanner = DirectoryScannerTool()

    target = tmp_path / "sample.txt"
    write_result = await writer.execute(path=str(target), content="hello")
    assert write_result.success is True

    read_result = await reader.execute(path=str(target))
    assert read_result.success is True
    assert read_result.data["content"] == "hello"

    scan_result = await scanner.execute(path=str(tmp_path))
    assert scan_result.success is True
    assert any(
        item.get("name") == "sample.txt" for item in scan_result.data.get("files", [])
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_tools_sqlite(tmp_path: Path) -> None:
    """Validate SQL query + inspector tools against a local sqlite db."""
    sqlalchemy = pytest.importorskip("sqlalchemy")
    del sqlalchemy

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO items (name) VALUES ('widget')")
    conn.commit()
    conn.close()

    connection_string = f"sqlite:///{db_path}"
    sql_tool = SQLQueryTool()
    inspector = DatabaseInspectorTool()

    query_result = await sql_tool.execute(
        query="SELECT name FROM items",
        connection_string=connection_string,
    )
    assert query_result.success is True
    assert query_result.data["row_count"] == 1

    inspect_result = await inspector.execute(
        connection_string=connection_string,
        operation="list_tables",
    )
    assert inspect_result.success is True
    assert "items" in inspect_result.data.get("tables", [])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_tools_with_mocked_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate web tools without external network calls."""
    httpx = pytest.importorskip("httpx")
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    api_tool = APICallerTool()
    http_tool = HTTPClientTool()

    api_result = await api_tool.execute(url="https://example.com", method="GET")
    assert api_result.success is True
    assert api_result.data["data"]["url"] == "https://example.com"

    http_result = await http_tool.execute(url="https://example.com")
    assert http_result.success is True
    assert http_result.data["status_code"] == 200