"""File watcher trigger implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from genxai.triggers.base import BaseTrigger

logger = logging.getLogger(__name__)


class FileWatcherTrigger(BaseTrigger):
    """Trigger that emits events on filesystem changes.

    Requires `watchdog` to be installed.
    """

    def __init__(
        self,
        trigger_id: str,
        watch_path: str | Path,
        recursive: bool = True,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(trigger_id=trigger_id, name=name)
        self.watch_path = Path(watch_path)
        self.recursive = recursive
        self._observer = None

    async def _start(self) -> None:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError as exc:
            raise ImportError(
                "watchdog is required for FileWatcherTrigger. Install with: pip install watchdog"
            ) from exc

        class _Handler(FileSystemEventHandler):
            def __init__(self, outer: "FileWatcherTrigger") -> None:
                self.outer = outer

            def on_any_event(self, event):
                payload: Dict[str, Any] = {
                    "event_type": event.event_type,
                    "src_path": event.src_path,
                    "is_directory": event.is_directory,
                }
                if getattr(event, "dest_path", None):
                    payload["dest_path"] = event.dest_path
                try:
                    import asyncio

                    asyncio.run_coroutine_threadsafe(
                        self.outer.emit(payload=payload),
                        asyncio.get_event_loop(),
                    )
                except Exception as exc:
                    logger.error("Failed to emit file event: %s", exc)

        handler = _Handler(self)
        observer = Observer()
        observer.schedule(handler, str(self.watch_path), recursive=self.recursive)
        observer.start()
        self._observer = observer
        logger.info("FileWatcherTrigger %s started", self.trigger_id)

    async def _stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        logger.info("FileWatcherTrigger %s stopped", self.trigger_id)