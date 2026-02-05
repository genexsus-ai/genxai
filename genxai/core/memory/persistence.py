"""Persistence helpers for memory modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import logging
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class MemoryPersistenceConfig:
    """Configuration for file-based memory persistence."""

    base_dir: Path
    enabled: bool = False
    backend: str = "json"  # "json" or "sqlite"
    sqlite_path: Optional[Path] = None

    def resolve(self, filename: str) -> Path:
        """Resolve a filename within the persistence directory."""
        return self.base_dir / filename

    def resolve_sqlite_path(self) -> Path:
        """Resolve SQLite database path."""
        if self.sqlite_path:
            return self.sqlite_path
        return self.base_dir / "memory.db"


class JsonMemoryStore:
    """Simple JSON file store for memory objects."""

    def __init__(self, config: MemoryPersistenceConfig) -> None:
        self.config = config

    def _ensure_dir(self) -> None:
        if not self.config.enabled:
            return
        self.config.base_dir.mkdir(parents=True, exist_ok=True)

    def load_list(self, filename: str) -> List[Dict[str, Any]]:
        """Load a list of dictionaries from disk."""
        if not self.config.enabled:
            return []

        path = self.config.resolve(filename)
        if not path.exists():
            return []

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return data
            logger.warning("Unexpected data format in %s", path)
            return []
        except Exception as exc:
            logger.error("Failed to load %s: %s", path, exc)
            return []

    def save_list(self, filename: str, items: Iterable[Dict[str, Any]]) -> None:
        """Save a list of dictionaries to disk."""
        if not self.config.enabled:
            return

        self._ensure_dir()
        path = self.config.resolve(filename)
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(list(items), file, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed to save %s: %s", path, exc)

    def load_mapping(self, filename: str) -> Dict[str, Any]:
        """Load a mapping from disk."""
        if not self.config.enabled:
            return {}

        path = self.config.resolve(filename)
        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                return data
            logger.warning("Unexpected data format in %s", path)
            return {}
        except Exception as exc:
            logger.error("Failed to load %s: %s", path, exc)
            return {}

    def save_mapping(self, filename: str, data: Dict[str, Any]) -> None:
        """Save a mapping to disk."""
        if not self.config.enabled:
            return

        self._ensure_dir()
        path = self.config.resolve(filename)
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, default=str)
        except Exception as exc:
            logger.error("Failed to save %s: %s", path, exc)


class SqliteMemoryStore:
    """SQLite-backed key/value store for memory persistence."""

    def __init__(self, config: MemoryPersistenceConfig) -> None:
        self.config = config
        self._initialized = False

    def _ensure_db(self) -> None:
        if not self.config.enabled:
            return
        if self._initialized:
            return
        self.config.base_dir.mkdir(parents=True, exist_ok=True)
        db_path = self.config.resolve_sqlite_path()
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_blobs (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS long_term_metadata (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT,
                    importance REAL,
                    timestamp TEXT,
                    tags TEXT,
                    metadata TEXT
                )
                """
            )
            conn.commit()
            self._initialized = True
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        self._ensure_db()
        return sqlite3.connect(self.config.resolve_sqlite_path())

    def load_list(self, filename: str) -> List[Dict[str, Any]]:
        if not self.config.enabled:
            return []

        self._ensure_db()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT payload FROM memory_blobs WHERE key = ?", (filename,))
            row = cursor.fetchone()
            if not row:
                return []
            data = json.loads(row[0])
            return data if isinstance(data, list) else []
        except Exception as exc:
            logger.error("Failed to load %s from sqlite: %s", filename, exc)
            return []
        finally:
            conn.close()

    def save_list(self, filename: str, items: Iterable[Dict[str, Any]]) -> None:
        if not self.config.enabled:
            return

        self._ensure_db()
        conn = self._get_connection()
        try:
            payload = json.dumps(list(items), default=str)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO memory_blobs (key, payload) VALUES (?, ?)",
                (filename, payload),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to save %s to sqlite: %s", filename, exc)
        finally:
            conn.close()

    def load_mapping(self, filename: str) -> Dict[str, Any]:
        if not self.config.enabled:
            return {}

        self._ensure_db()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT payload FROM memory_blobs WHERE key = ?", (filename,))
            row = cursor.fetchone()
            if not row:
                return {}
            data = json.loads(row[0])
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.error("Failed to load %s from sqlite: %s", filename, exc)
            return {}
        finally:
            conn.close()

    def save_mapping(self, filename: str, data: Dict[str, Any]) -> None:
        if not self.config.enabled:
            return

        self._ensure_db()
        conn = self._get_connection()
        try:
            payload = json.dumps(data, default=str)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO memory_blobs (key, payload) VALUES (?, ?)",
                (filename, payload),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to save %s to sqlite: %s", filename, exc)
        finally:
            conn.close()

    def store_long_term_metadata(
        self,
        memory_id: str,
        memory_type: str,
        importance: float,
        timestamp: str,
        tags: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        if not self.config.enabled:
            return

        self._ensure_db()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO long_term_metadata
                (memory_id, memory_type, importance, timestamp, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    memory_type,
                    importance,
                    timestamp,
                    ",".join(tags),
                    json.dumps(metadata, default=str),
                ),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to store long-term metadata: %s", exc)
        finally:
            conn.close()

    def delete_long_term_metadata(self, memory_id: str) -> None:
        if not self.config.enabled:
            return

        self._ensure_db()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM long_term_metadata WHERE memory_id = ?",
                (memory_id,),
            )
            conn.commit()
        except Exception as exc:
            logger.error("Failed to delete long-term metadata: %s", exc)
        finally:
            conn.close()


def create_memory_store(config: MemoryPersistenceConfig) -> JsonMemoryStore | SqliteMemoryStore:
    """Factory for memory stores based on config backend."""
    if config.backend == "sqlite":
        return SqliteMemoryStore(config)
    return JsonMemoryStore(config)