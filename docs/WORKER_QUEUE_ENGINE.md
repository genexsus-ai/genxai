# Worker Queue Engine

The **WorkerQueueEngine** provides a minimal async worker pool for running workflow tasks
in a queued, distributed‑friendly way. It uses an in‑memory backend by default and is
designed to be swapped with Redis/Celery/RQ implementations later.

## Quick Start

```python
from genxai.core.execution import WorkerQueueEngine

engine = WorkerQueueEngine(worker_count=4)

async def handler(payload: dict):
    print("processing", payload)

await engine.start()
task_id = await engine.enqueue({"workflow_id": "wf_1"}, handler)
await engine.stop()
```

## Notes
- The current backend is in‑memory (`InMemoryQueueBackend`).
- Redis-backed queues are supported via `RedisQueueBackend` (requires `redis`).
- Use `WorkerQueueEngine.enqueue` to push work.
- Provide `run_id` to enable idempotent enqueues.
- Retries use linear backoff via `max_retries` + `backoff_seconds`.
- Hooks for persistent backends can implement `QueueBackend`.

## Redis Backend Example

```python
from genxai.core.execution import WorkerQueueEngine, RedisQueueBackend

backend = RedisQueueBackend(url="redis://localhost:6379/0")
engine = WorkerQueueEngine(backend=backend)

async def handler(payload: dict):
    print("processing", payload)

engine.register_handler("workflow", handler)
await engine.start()
await engine.enqueue({"workflow_id": "wf_1"}, handler_name="workflow")
```