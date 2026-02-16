"""Trigger registry for managing workflow triggers."""

from __future__ import annotations

from typing import Dict, List, Optional
import logging

from genxai.triggers.base import BaseTrigger, TriggerStatus

logger = logging.getLogger(__name__)


class TriggerRegistry:
    """Central registry for triggers."""

    _instance: Optional["TriggerRegistry"] = None
    _triggers: Dict[str, BaseTrigger] = {}

    def __new__(cls) -> "TriggerRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, trigger: BaseTrigger) -> None:
        """Register a trigger instance."""
        if trigger.trigger_id in cls._triggers:
            logger.warning("Trigger %s already registered, overwriting", trigger.trigger_id)
        cls._triggers[trigger.trigger_id] = trigger
        logger.info("Registered trigger: %s", trigger.trigger_id)

    @classmethod
    def unregister(cls, trigger_id: str) -> None:
        """Unregister a trigger by id."""
        trigger = cls._triggers.pop(trigger_id, None)
        if trigger:
            logger.info("Unregistered trigger: %s", trigger_id)
        else:
            logger.warning("Trigger %s not found in registry", trigger_id)

    @classmethod
    def get(cls, trigger_id: str) -> Optional[BaseTrigger]:
        """Get a trigger by id."""
        return cls._triggers.get(trigger_id)

    @classmethod
    def list_all(cls) -> List[BaseTrigger]:
        """List all registered triggers."""
        return list(cls._triggers.values())

    @classmethod
    def clear(cls) -> None:
        """Clear all triggers from the registry."""
        cls._triggers.clear()
        logger.info("Cleared all triggers from registry")

    @classmethod
    async def start_all(cls) -> None:
        """Start all registered triggers."""
        for trigger in cls._triggers.values():
            if trigger.status != TriggerStatus.RUNNING:
                await trigger.start()

    @classmethod
    async def stop_all(cls) -> None:
        """Stop all registered triggers."""
        for trigger in cls._triggers.values():
            if trigger.status != TriggerStatus.STOPPED:
                await trigger.stop()

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Return registry stats by trigger status."""
        stats: Dict[str, int] = {}
        for trigger in cls._triggers.values():
            status = trigger.status.value
            stats[status] = stats.get(status, 0) + 1
        stats["total"] = len(cls._triggers)
        return stats

    def __repr__(self) -> str:
        return f"TriggerRegistry(triggers={len(self._triggers)})"