"""State manager for workflow execution."""

import json
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import logging

from genxai.core.state.schema import StateSchema

logger = logging.getLogger(__name__)


class StateManager:
    """Manages workflow state with persistence and versioning."""

    def __init__(
        self,
        schema: Optional[StateSchema] = None,
        enable_persistence: bool = False,
        persistence_path: Optional[Path] = None,
    ) -> None:
        """Initialize state manager.

        Args:
            schema: State schema for validation
            enable_persistence: Whether to enable state persistence
            persistence_path: Path for state persistence
        """
        self.schema = schema
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path or Path(".genxai/state")
        self._state: Dict[str, Any] = {}
        self._history: list[Dict[str, Any]] = []
        self._version = 0

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in state.

        Args:
            key: State key
            value: Value to set
        """
        old_value = self._state.get(key)
        self._state[key] = value
        self._version += 1

        # Record in history
        self._history.append(
            {
                "version": self._version,
                "timestamp": datetime.now().isoformat(),
                "action": "set",
                "key": key,
                "old_value": old_value,
                "new_value": value,
            }
        )

        logger.debug(f"State updated: {key} = {value}")

        # Persist if enabled
        if self.enable_persistence:
            self._persist()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values.

        Args:
            updates: Dictionary of updates
        """
        for key, value in updates.items():
            self.set(key, value)

    def delete(self, key: str) -> None:
        """Delete key from state.

        Args:
            key: State key to delete
        """
        if key in self._state:
            old_value = self._state[key]
            del self._state[key]
            self._version += 1

            self._history.append(
                {
                    "version": self._version,
                    "timestamp": datetime.now().isoformat(),
                    "action": "delete",
                    "key": key,
                    "old_value": old_value,
                }
            )

            logger.debug(f"State key deleted: {key}")

            if self.enable_persistence:
                self._persist()

    def get_all(self) -> Dict[str, Any]:
        """Get all state values.

        Returns:
            Complete state dictionary
        """
        return self._state.copy()

    def clear(self) -> None:
        """Clear all state."""
        self._state.clear()
        self._version += 1
        self._history.append(
            {
                "version": self._version,
                "timestamp": datetime.now().isoformat(),
                "action": "clear",
            }
        )
        logger.info("State cleared")

        if self.enable_persistence:
            self._persist()

    def validate(self) -> bool:
        """Validate current state against schema.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if self.schema is None:
            return True

        return self.schema.validate_state(self._state)

    def checkpoint(self, name: str) -> None:
        """Create a named checkpoint of current state.

        Args:
            name: Checkpoint name
        """
        checkpoint = {
            "name": name,
            "version": self._version,
            "timestamp": datetime.now().isoformat(),
            "state": self._state.copy(),
        }

        self._history.append(
            {
                "version": self._version,
                "timestamp": datetime.now().isoformat(),
                "action": "checkpoint",
                "checkpoint": checkpoint,
            }
        )

        logger.info(f"Checkpoint created: {name}")

        if self.enable_persistence:
            self._persist_checkpoint(name, checkpoint)

    def rollback(self, version: Optional[int] = None) -> None:
        """Rollback state to a previous version.

        Args:
            version: Version to rollback to (default: previous version)
        """
        if not self._history:
            logger.warning("No history to rollback to")
            return

        target_version = version or (self._version - 1)

        # Find state at target version
        for entry in reversed(self._history):
            if entry.get("version") == target_version:
                if entry.get("action") == "checkpoint":
                    self._state = entry["checkpoint"]["state"].copy()
                    self._version = target_version
                    logger.info(f"Rolled back to version {target_version}")
                    return

        logger.warning(f"Version {target_version} not found in history")

    def get_history(self, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        """Get state change history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries
        """
        if limit:
            return self._history[-limit:]
        return self._history.copy()

    def _persist(self) -> None:
        """Persist current state to disk."""
        if not self.persistence_path:
            return

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        state_file = self.persistence_path / "current_state.json"

        try:
            with open(state_file, "w") as f:
                json.dump(
                    {
                        "version": self._version,
                        "timestamp": datetime.now().isoformat(),
                        "state": self._state,
                    },
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug(f"State persisted to {state_file}")
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")

    def _persist_checkpoint(self, name: str, checkpoint: Dict[str, Any]) -> None:
        """Persist a checkpoint to disk.

        Args:
            name: Checkpoint name
            checkpoint: Checkpoint data
        """
        if not self.persistence_path:
            return

        self.persistence_path.mkdir(parents=True, exist_ok=True)
        checkpoint_file = self.persistence_path / f"checkpoint_{name}.json"

        try:
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2, default=str)
            logger.debug(f"Checkpoint persisted to {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to persist checkpoint: {e}")

    def load(self, path: Optional[Path] = None) -> None:
        """Load state from disk.

        Args:
            path: Path to load from (default: persistence_path)
        """
        load_path = path or (self.persistence_path / "current_state.json")

        if not load_path.exists():
            logger.warning(f"State file not found: {load_path}")
            return

        try:
            with open(load_path, "r") as f:
                data = json.load(f)
                self._state = data.get("state", {})
                self._version = data.get("version", 0)
            logger.info(f"State loaded from {load_path}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert state manager to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "version": self._version,
            "state": self._state,
            "history_length": len(self._history),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"StateManager(version={self._version}, keys={len(self._state)})"
