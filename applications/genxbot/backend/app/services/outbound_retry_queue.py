"""Background retry queue for failed outbound channel deliveries."""

from __future__ import annotations

import time
from collections import deque
from threading import Event, Lock, Thread
from typing import Callable
from uuid import uuid4

from app.schemas import OutboundRetryJob, OutboundRetryQueueSnapshot


class OutboundRetryQueueService:
    """Retries failed outbound sends and stores dead letters."""

    def __init__(
        self,
        *,
        send_fn: Callable[[str, str, str, str | None], str],
        worker_enabled: bool,
        max_attempts: int,
        backoff_seconds: float,
    ) -> None:
        self._send_fn = send_fn
        self._max_attempts = max(max_attempts, 1)
        self._backoff_seconds = max(backoff_seconds, 0.0)
        self._queue: deque[OutboundRetryJob] = deque()
        self._dead_letters: list[OutboundRetryJob] = []
        self._lock = Lock()
        self._stop = Event()
        self._worker: Thread | None = None

        if worker_enabled:
            self._worker = Thread(target=self._loop, daemon=True)
            self._worker.start()

    def enqueue(self, *, channel: str, channel_id: str, text: str, thread_id: str | None = None) -> OutboundRetryJob:
        job = OutboundRetryJob(
            id=f"out_{uuid4().hex[:10]}",
            channel=channel,
            channel_id=channel_id,
            text=text,
            thread_id=thread_id,
            max_attempts=self._max_attempts,
        )
        with self._lock:
            self._queue.append(job)
        return job

    def snapshot(self) -> OutboundRetryQueueSnapshot:
        with self._lock:
            return OutboundRetryQueueSnapshot(
                queued=len(self._queue),
                dead_lettered=len(self._dead_letters),
                dead_letters=list(self._dead_letters),
            )

    def _loop(self) -> None:
        while not self._stop.is_set():
            job: OutboundRetryJob | None = None
            with self._lock:
                if self._queue:
                    job = self._queue.popleft()

            if not job:
                time.sleep(0.05)
                continue

            status = self._send_fn(job.channel, job.channel_id, job.text, job.thread_id)
            if status.startswith("sent:"):
                continue

            job.attempts += 1
            job.last_error = status
            if job.attempts >= job.max_attempts:
                with self._lock:
                    self._dead_letters.append(job)
            else:
                time.sleep(self._backoff_seconds)
                with self._lock:
                    self._queue.append(job)

    def stop(self) -> None:
        self._stop.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1)
