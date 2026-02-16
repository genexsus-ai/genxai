"""Integration-style tests for encrypted connector config storage."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

from genxai_enterprise.connectors.config_store import ConnectorConfigEntry, ConnectorConfigStore


class FakeFernet:
    def __init__(self, key: bytes) -> None:
        self.key = key

    def encrypt(self, payload: bytes) -> bytes:
        return b"enc:" + payload

    def decrypt(self, payload: bytes) -> bytes:
        if not payload.startswith(b"enc:"):
            raise ValueError("invalid payload")
        return payload[4:]


def test_encrypted_config_store_roundtrip(tmp_path: Path, monkeypatch) -> None:
    fake_module = SimpleNamespace(Fernet=FakeFernet)
    sys.modules["cryptography"] = SimpleNamespace(fernet=fake_module)
    sys.modules["cryptography.fernet"] = fake_module

    store = ConnectorConfigStore(path=tmp_path / "configs.json", encryption_key="dummy")
    entry = ConnectorConfigEntry(
        name="slack_alerts",
        connector_type="slack",
        config={"bot_token": "xoxb"},
    )
    store.save(entry)

    raw = (tmp_path / "configs.json").read_text()
    assert "encrypted" in raw

    fetched = store.get("slack_alerts")
    assert fetched is not None
    assert fetched.config["bot_token"] == "xoxb"