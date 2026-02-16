"""CLI tests for connector commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import builtins
import sys
from types import SimpleNamespace

from click.testing import CliRunner

from enterprise.cli.commands.connector import connector as connector_group, CONNECTOR_CATALOG


@dataclass
class DummyConnector:
    connector_id: str
    required_value: str
    started: bool = False
    stopped: bool = False

    async def validate_config(self) -> None:
        if not self.required_value:
            raise ValueError("missing")

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def health_check(self) -> Dict[str, Any]:
        return {"connector_id": self.connector_id, "status": "ok"}


def test_connector_list_json() -> None:
    runner = CliRunner()
    result = runner.invoke(connector_group, ["list", "--format", "json"])
    assert result.exit_code == 0
    assert "slack" in result.output


def test_connector_validate_start_stop_health(monkeypatch) -> None:
    runner = CliRunner()
    dummy_meta = {
        "class": DummyConnector,
        "required": ["required_value"],
        "description": "Dummy",
    }

    monkeypatch.setitem(CONNECTOR_CATALOG, "dummy", dummy_meta)

    config = '{"required_value": "ok"}'
    validate = runner.invoke(connector_group, ["validate", "--type", "dummy", "--config", config])
    assert validate.exit_code == 0
    assert "configuration valid" in validate.output.lower()

    start = runner.invoke(connector_group, ["start", "--type", "dummy", "--config", config])
    assert start.exit_code == 0
    assert "started" in start.output.lower()

    stop = runner.invoke(connector_group, ["stop", "--type", "dummy", "--config", config])
    assert stop.exit_code == 0
    assert "stopped" in stop.output.lower()

    health = runner.invoke(connector_group, ["health", "--type", "dummy", "--config", config])
    assert health.exit_code == 0
    assert "connector_id" in health.output

    monkeypatch.delitem(CONNECTOR_CATALOG, "dummy")


def test_connector_error_cases() -> None:
    runner = CliRunner()
    bad_type = runner.invoke(connector_group, ["validate", "--type", "missing"])
    assert bad_type.exit_code != 0
    assert "unknown connector type" in bad_type.output.lower()

    missing_fields = runner.invoke(connector_group, ["validate", "--type", "slack", "--config", "{}"])
    assert missing_fields.exit_code != 0
    assert "missing required fields" in missing_fields.output.lower()

    missing_saved = runner.invoke(
        connector_group, ["health", "--type", "slack", "--config-name", "nope"]
    )
    assert missing_saved.exit_code != 0
    assert "config 'nope' not found" in missing_saved.output.lower()


def test_connector_keygen(monkeypatch) -> None:
    runner = CliRunner()

    class FakeFernet:
        @staticmethod
        def generate_key():
            return b"fake-key"

    monkeypatch.setitem(sys.modules, "cryptography", SimpleNamespace(fernet=SimpleNamespace(Fernet=FakeFernet)))
    monkeypatch.setitem(sys.modules, "cryptography.fernet", SimpleNamespace(Fernet=FakeFernet))

    result = runner.invoke(connector_group, ["keygen"])
    assert result.exit_code == 0
    assert "fake-key" in result.output


def test_connector_keygen_missing_dependency(monkeypatch) -> None:
    runner = CliRunner()

    if "cryptography" in sys.modules:
        monkeypatch.delitem(sys.modules, "cryptography", raising=False)
    if "cryptography.fernet" in sys.modules:
        monkeypatch.delitem(sys.modules, "cryptography.fernet", raising=False)

    original_import = builtins.__import__

    def blocked_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("cryptography"):
            raise ImportError("No module named 'cryptography'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    result = runner.invoke(connector_group, ["keygen"])
    assert result.exit_code != 0
    assert "cryptography is required" in result.output.lower()