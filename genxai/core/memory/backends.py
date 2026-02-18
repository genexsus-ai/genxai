"""Formal memory backend plugins and telemetry helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import logging
import sqlite3

logger = logging.getLogger(__name__)


class MemoryBackendPlugin(ABC):
    """Base contract for pluggable memory backends."""

    def __init__(self, backend: str) -> None:
        self.backend = backend

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return backend-specific telemetry and utilization stats."""


class MemoryBackendRegistry:
    """Registry/factory for memory backend plugins."""

    _factories: Dict[str, Callable[..., MemoryBackendPlugin]] = {}

    @classmethod
    def register(cls, name: str, factory: Callable[..., MemoryBackendPlugin]) -> None:
        cls._factories[name] = factory

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> MemoryBackendPlugin:
        if name not in cls._factories:
            raise ValueError(
                f"Unsupported memory backend plugin: {name}. "
                f"Supported: {list(cls._factories.keys())}"
            )
        return cls._factories[name](**kwargs)

    @classmethod
    def list_backends(cls) -> List[str]:
        return list(cls._factories.keys())


class RedisMemoryBackendPlugin(MemoryBackendPlugin):
    """Redis backend plugin with memory telemetry."""

    def __init__(self, redis_client: Any, key_prefix: str = "genxai:memory:") -> None:
        super().__init__(backend="redis")
        self._redis = redis_client
        self._key_prefix = key_prefix

    def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "backend": self.backend,
            "available": self._redis is not None,
        }
        if self._redis is None:
            return stats

        try:
            info = self._redis.info("memory")
        except Exception:
            try:
                info = self._redis.info()
            except Exception as exc:
                stats["error"] = str(exc)
                return stats

        used = info.get("used_memory")
        max_memory = info.get("maxmemory")
        if max_memory in (0, "0"):
            max_memory = None

        key_count: Optional[int]
        try:
            key_count = len(self._redis.keys(f"{self._key_prefix}*"))
        except Exception:
            key_count = None

        utilization = None
        if isinstance(used, (int, float)) and isinstance(max_memory, (int, float)) and max_memory > 0:
            utilization = used / max_memory

        stats.update(
            {
                "memory_size_bytes": used,
                "memory_max_bytes": max_memory,
                "utilization": utilization,
                "key_count": key_count,
            }
        )
        return stats


class SqliteMemoryBackendPlugin(MemoryBackendPlugin):
    """SQLite backend plugin with file and table telemetry."""

    def __init__(self, sqlite_path: Path | str) -> None:
        super().__init__(backend="sqlite")
        self._sqlite_path = Path(sqlite_path)

    def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "backend": self.backend,
            "path": str(self._sqlite_path),
            "available": self._sqlite_path.exists(),
            "file_size_bytes": self._sqlite_path.stat().st_size if self._sqlite_path.exists() else 0,
        }
        if not self._sqlite_path.exists():
            return stats

        conn = sqlite3.connect(self._sqlite_path)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA page_count")
            page_count = int(cursor.fetchone()[0])
            cursor.execute("PRAGMA page_size")
            page_size = int(cursor.fetchone()[0])

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_names = [row[0] for row in cursor.fetchall()]

            table_rows: Dict[str, Optional[int]] = {}
            for table in table_names:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_rows[table] = int(cursor.fetchone()[0])
                except Exception:
                    table_rows[table] = None

            stats.update(
                {
                    "db_size_bytes": page_count * page_size,
                    "table_count": len(table_names),
                    "table_rows": table_rows,
                }
            )
        except Exception as exc:
            stats["error"] = str(exc)
        finally:
            conn.close()

        return stats


class Neo4jMemoryBackendPlugin(MemoryBackendPlugin):
    """Neo4j backend plugin with graph and traversal telemetry."""

    def __init__(self, graph_db: Any, traversal_depth: int = 2) -> None:
        super().__init__(backend="neo4j")
        self._graph_db = graph_db
        self._traversal_depth = traversal_depth

    def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "backend": self.backend,
            "available": self._graph_db is not None,
            "traversal_depth": self._traversal_depth,
        }
        if self._graph_db is None:
            return stats

        try:
            with self._graph_db.session() as session:
                node_record = session.run("MATCH (n) RETURN count(n) AS node_count")
                edge_record = session.run("MATCH ()-[r]->() RETURN count(r) AS edge_count")

                node_row = next(iter(node_record), None)
                edge_row = next(iter(edge_record), None)

                node_count = self._record_get(node_row, "node_count", 0)
                edge_count = self._record_get(edge_row, "edge_count", 0)

                stats["graph_size"] = {
                    "node_count": int(node_count or 0),
                    "edge_count": int(edge_count or 0),
                }

                stats["avg_out_degree"] = (
                    (int(edge_count) / int(node_count))
                    if node_count not in (None, 0)
                    else 0.0
                )

                traversal_query = """
                MATCH (n)
                WITH n LIMIT 1
                OPTIONAL MATCH p=(n)-[*1..$depth]->(m)
                RETURN count(p) AS traversal_path_count, count(DISTINCT m) AS traversal_reachable_nodes
                """
                traversal_record = session.run(traversal_query, depth=self._traversal_depth)
                traversal_row = next(iter(traversal_record), None)
                stats["traversal"] = {
                    "path_count": int(self._record_get(traversal_row, "traversal_path_count", 0) or 0),
                    "reachable_nodes": int(
                        self._record_get(traversal_row, "traversal_reachable_nodes", 0) or 0
                    ),
                }
        except Exception as exc:
            stats["error"] = str(exc)

        return stats

    @staticmethod
    def _record_get(record: Any, key: str, default: Any = None) -> Any:
        if record is None:
            return default
        if isinstance(record, dict):
            return record.get(key, default)
        try:
            value = record.get(key)
            return default if value is None else value
        except Exception:
            return default


# Register built-in plugins
MemoryBackendRegistry.register("redis", RedisMemoryBackendPlugin)
MemoryBackendRegistry.register("sqlite", SqliteMemoryBackendPlugin)
MemoryBackendRegistry.register("neo4j", Neo4jMemoryBackendPlugin)
