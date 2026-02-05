"""Unit tests for memory persistence backends."""

from pathlib import Path

from genxai.core.memory.persistence import (
    MemoryPersistenceConfig,
    JsonMemoryStore,
    SqliteMemoryStore,
    create_memory_store,
)


def test_json_memory_store_save_and_load(tmp_path: Path) -> None:
    config = MemoryPersistenceConfig(base_dir=tmp_path, enabled=True, backend="json")
    store = JsonMemoryStore(config)
    items = [{"id": "1", "value": "alpha"}]
    store.save_list("items.json", items)
    assert store.load_list("items.json") == items


def test_json_memory_store_mapping(tmp_path: Path) -> None:
    config = MemoryPersistenceConfig(base_dir=tmp_path, enabled=True, backend="json")
    store = JsonMemoryStore(config)
    mapping = {"foo": "bar"}
    store.save_mapping("map.json", mapping)
    assert store.load_mapping("map.json") == mapping


def test_sqlite_memory_store_roundtrip(tmp_path: Path) -> None:
    config = MemoryPersistenceConfig(base_dir=tmp_path, enabled=True, backend="sqlite")
    store = SqliteMemoryStore(config)
    items = [{"id": "1", "value": "alpha"}]
    store.save_list("items", items)
    assert store.load_list("items") == items
    mapping = {"foo": "bar"}
    store.save_mapping("map", mapping)
    assert store.load_mapping("map") == mapping


def test_create_memory_store_factory(tmp_path: Path) -> None:
    config = MemoryPersistenceConfig(base_dir=tmp_path, enabled=True, backend="sqlite")
    store = create_memory_store(config)
    assert isinstance(store, SqliteMemoryStore)
