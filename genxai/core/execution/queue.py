"""Async worker queue engine for distributed execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Protocol
import uuid
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class QueueTask:
    """Represents a unit of work for the worker queue."""

    task_id: str
    payload: dict[str, Any]
    handler: Optional[Callable[[dict[str, Any]], Awaitable[Any]]]
    metadata: dict[str, Any] = field(default_factory=dict)


class QueueBackend(Protocol):
    """Protocol for queue backends."""

    async def put(self, task: QueueTask) -> None:
        ...

    async def get(self) -> QueueTask:
        ...

    def qsize(self) -> int:
        ...


class InMemoryQueueBackend:
    """In-memory asyncio queue backend."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[QueueTask] = asyncio.Queue()

    async def put(self, task: QueueTask) -> None:
        await self._queue.put(task)

    async def get(self) -> QueueTask:
        return await self._queue.get()

    def qsize(self) -> int:
        return self._queue.qsize()


class WorkerQueueEngine:
    """Simple async worker engine for processing queued tasks."""

    def __init__(
        self,
        backend: Optional[QueueBackend] = None,
        worker_count: int = 2,
        max_retries: int = 3,
        backoff_seconds: float = 0.5,
        handler_registry: Optional[dict[str, Callable[[dict[str, Any]], Awaitable[Any]]]] = None,
    ) -> None:
        self._backend = backend or InMemoryQueueBackend()
        self._worker_count = worker_count
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._workers: list[asyncio.Task[None]] = []
        self._running = False
        self._handler_registry = handler_registry or {}

    def register_handler(
        self,
        name: str,
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> None:
        """Register a handler by name for distributed queue backends."""
        self._handler_registry[name] = handler

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for idx in range(self._worker_count):
            worker = asyncio.create_task(self._worker_loop(idx))
            self._workers.append(worker)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(
        self,
        payload: dict[str, Any],
        handler: Optional[Callable[[dict[str, Any]], Awaitable[Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
        run_id: Optional[str] = None,
        handler_name: Optional[str] = None,
    ) -> str:
        task_id = run_id or str(uuid.uuid4())
        if handler is None and handler_name:
            handler = self._handler_registry.get(handler_name)
        if handler is None:
            raise ValueError("Handler must be provided or registered via handler_name")
        task = QueueTask(
            task_id=task_id,
            payload=payload,
            handler=handler,
            metadata={**(metadata or {}), "handler_name": handler_name},
        )
        await self._backend.put(task)
        return task_id

    async def _worker_loop(self, worker_id: int) -> None:
        while self._running:
            try:
                task = await self._backend.get()
                await self._execute_with_retry(task)
                logger.debug(
                    "Worker %s processed task %s", worker_id, task.task_id
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Worker %s failed: %s", worker_id, exc)

    async def _execute_with_retry(self, task: QueueTask) -> None:
        handler = task.handler
        if handler is None:
            handler_name = task.metadata.get("handler_name")
            handler = self._handler_registry.get(handler_name) if handler_name else None
        if handler is None:
            raise ValueError(f"No handler registered for task {task.task_id}")
        attempts = 0
        while True:
            try:
                await handler(task.payload)
                return
            except Exception as exc:
                attempts += 1
                if attempts > self._max_retries:
                    raise exc
                await asyncio.sleep(self._backoff_seconds * attempts)


class RedisQueueBackend:
    """Redis-backed queue backend for distributed execution.

    Stores serialized QueueTask payloads in a Redis list and uses BLPOP to
    retrieve work items.
    """

    def __init__(self, url: str, queue_name: str = "genxai:queue") -> None:
        try:
            import redis.asyncio as redis  # type: ignore
        except Exception as exc:
            raise ImportError(
                "redis package is required for RedisQueueBackend. Install with: pip install redis"
            ) from exc

        self._redis = redis.from_url(url)
        self._queue_name = queue_name

    async def put(self, task: QueueTask) -> None:
        payload = {
            "task_id": task.task_id,
            "payload": task.payload,
            "metadata": task.metadata,
        }
        await self._redis.rpush(self._queue_name, json.dumps(payload))

    async def get(self) -> QueueTask:
        _, raw = await self._redis.blpop(self._queue_name)
        data = json.loads(raw)
        return QueueTask(
            task_id=data["task_id"],
            payload=data["payload"],
            handler=None,
            metadata=data.get("metadata", {}),
        )

    def qsize(self) -> int:
        return int(self._redis.llen(self._queue_name))


class RQQueueBackend:
    """Placeholder backend for Redis/RQ integration.

    This is a stub that documents the interface needed for an RQ backend.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "RQQueueBackend is a stub. Implement with Redis + rq when ready."
        )