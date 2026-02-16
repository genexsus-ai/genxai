"""Unit tests for ConnectorConfigStore."""

from __future__ import annotations

from pathlib import Path

import pytest

from enterprise.genxai.connectors.config_store import ConnectorConfigEntry, ConnectorConfigStore


def test_config_store_save_get_delete(tmp_path: Path) -> None:
    store = ConnectorConfigStore(path=tmp_path / "configs.json")
    entry = ConnectorConfigEntry(
        name="slack_alerts",
        connector_type="slack",
        config={"bot_token": "xoxb"},
    )
    store.save(entry)

    fetched = store.get("slack_alerts")
    assert fetched is not None
    assert fetched.connector_type == "slack"
    assert fetched.config["bot_token"] == "xoxb"

    listed = store.list()
    assert "slack_alerts" in listed

    removed = store.delete("slack_alerts")
    assert removed is True
    assert store.get("slack_alerts") is None


def test_config_store_encryption_roundtrip(monkeypatch, tmp_path: Path) -> None:
    store = ConnectorConfigStore(path=tmp_path / "configs.json", encryption_key="dummy")

    monkeypatch.setattr(store, "_encrypt", lambda payload: payload)
    monkeypatch.setattr(store, "_decrypt", lambda payload: payload)

    entry = ConnectorConfigEntry(
        name="slack_alerts",
        connector_type="slack",
        config={"bot_token": "xoxb"},
    )
    store.save(entry)

    raw = (tmp_path / "configs.json").read_text()
    assert "\"encrypted\": true" in raw.lower()

    fetched = store.get("slack_alerts")
    assert fetched is not None
    assert fetched.config["bot_token"] == "xoxb"