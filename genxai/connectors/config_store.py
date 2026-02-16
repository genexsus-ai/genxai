"""Connector configuration persistence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os


@dataclass
class ConnectorConfigEntry:
    name: str
    connector_type: str
    config: Dict[str, Any]


class ConnectorConfigStore:
    """Persist connector configurations as JSON on disk.

    Supports optional encryption when a key is provided via the
    `GENXAI_CONNECTOR_CONFIG_KEY` environment variable or `encryption_key`.
    """

    def __init__(self, path: Optional[Path] = None, encryption_key: Optional[str] = None) -> None:
        self.path = path or Path(".genxai/connectors.json")
        self.encryption_key = encryption_key or os.getenv("GENXAI_CONNECTOR_CONFIG_KEY")

    def list(self) -> Dict[str, ConnectorConfigEntry]:
        data = self._read_raw()
        return {
            name: ConnectorConfigEntry(
                name=name,
                connector_type=payload["connector_type"],
                config=payload.get("config", {}),
            )
            for name, payload in data.items()
        }

    def get(self, name: str) -> Optional[ConnectorConfigEntry]:
        data = self._read_raw()
        payload = data.get(name)
        if not payload:
            return None
        return ConnectorConfigEntry(
            name=name,
            connector_type=payload["connector_type"],
            config=payload.get("config", {}),
        )

    def save(self, entry: ConnectorConfigEntry) -> None:
        data = self._read_raw()
        data[entry.name] = {
            "connector_type": entry.connector_type,
            "config": entry.config,
        }
        self._write_raw(data)

    def delete(self, name: str) -> bool:
        data = self._read_raw()
        if name not in data:
            return False
        data.pop(name)
        self._write_raw(data)
        return True

    def _read_raw(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text())
        if isinstance(raw, dict) and raw.get("encrypted"):
            payload = raw.get("payload")
            if not payload:
                raise ValueError("Encrypted connector config missing payload")
            return json.loads(self._decrypt(payload))
        return raw

    def _write_raw(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.encryption_key:
            encrypted = self._encrypt(json.dumps(data))
            payload = {"encrypted": True, "payload": encrypted}
            self.path.write_text(json.dumps(payload, indent=2))
            return
        self.path.write_text(json.dumps(data, indent=2))

    def _get_fernet(self):
        if not self.encryption_key:
            raise ValueError("Encryption key not configured")
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise ImportError(
                "cryptography is required for encrypted connector configs. "
                "Install with: pip install cryptography"
            ) from exc
        return Fernet(self.encryption_key.encode())

    def _encrypt(self, payload: str) -> str:
        fernet = self._get_fernet()
        return fernet.encrypt(payload.encode()).decode()

    def _decrypt(self, payload: str) -> str:
        fernet = self._get_fernet()
        return fernet.decrypt(payload.encode()).decode()