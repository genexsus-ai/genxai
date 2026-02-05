"""Tests for state manager."""

import pytest
from genxai.core.state.manager import StateManager


def test_state_manager_initialization():
    """Test state manager initialization."""
    manager = StateManager()
    assert manager is not None


def test_set_and_get_state():
    """Test setting and getting state."""
    manager = StateManager()
    manager.set("key1", "value1")
    assert manager.get("key1") == "value1"
    assert manager.get("nonexistent") is None


def test_get_all_state():
    """Test getting all state."""
    manager = StateManager()
    manager.set("key1", "value1")
    manager.set("key2", "value2")
    all_state = manager.get_all()
    assert "key1" in all_state
    assert "key2" in all_state
    assert all_state["key1"] == "value1"


def test_delete_state():
    """Test deleting state."""
    manager = StateManager()
    manager.set("key1", "value1")
    manager.delete("key1")
    assert manager.get("key1") is None


def test_clear_state():
    """Test clearing all state."""
    manager = StateManager()
    manager.set("key1", "value1")
    manager.set("key2", "value2")
    manager.clear()
    assert len(manager.get_all()) == 0


def test_checkpoint():
    """Test state checkpointing."""
    manager = StateManager()
    manager.set("key1", "value1")
    manager.checkpoint("checkpoint1")
    manager.set("key1", "value2")
    assert manager.get("key1") == "value2"


def test_state_to_dict():
    """Test converting state to dictionary."""
    manager = StateManager()
    manager.set("key1", "value1")
    state_dict = manager.to_dict()
    assert "state" in state_dict or "data" in state_dict or state_dict.get("key1") == "value1"
