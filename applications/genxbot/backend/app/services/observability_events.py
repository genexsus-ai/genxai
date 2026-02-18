"""Structured observability event service for GenXBot workflows."""

from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Optional

from app.schemas import ObservabilityEvent, ObservabilityEventsPage, ObservabilitySnapshot

from genxai.observability.metrics import get_metrics_collector
from genxai.observability.tracing import add_event


class ObservabilityEventService:
    """Captures structured operational events and lightweight aggregates."""

    def __init__(
        self,
        max_entries: int = 5000,
        default_sample_rate: float = 1.0,
        per_key_rate_limit_per_minute: int = 240,
        max_attributes: int = 25,
        attribute_key_max_length: int = 64,
        attribute_value_max_length: int = 256,
        sample_overrides: Optional[dict[str, float]] = None,
    ) -> None:
        self._max_entries = max(max_entries, 1)
        self._events: deque[ObservabilityEvent] = deque(maxlen=self._max_entries)
        self._lock = Lock()
        self._default_sample_rate = min(max(default_sample_rate, 0.0), 1.0)
        self._per_key_rate_limit_per_minute = max(per_key_rate_limit_per_minute, 1)
        self._max_attributes = max(max_attributes, 0)
        self._attribute_key_max_length = max(attribute_key_max_length, 8)
        self._attribute_value_max_length = max(attribute_value_max_length, 32)
        self._sample_overrides = {k: min(max(v, 0.0), 1.0) for k, v in (sample_overrides or {}).items()}
        self._emit_counter = 0
        self._rate_window_key: str = ""
        self._rate_counts: dict[str, int] = {}

    @staticmethod
    def _parse_ts(timestamp: str) -> Optional[datetime]:
        try:
            dt = datetime.fromisoformat(timestamp)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def _sanitize_attributes(self, attributes: Optional[dict[str, Any]]) -> dict[str, Any]:
        if not attributes or self._max_attributes <= 0:
            return {}
        clean: dict[str, Any] = {}
        for idx, (key, value) in enumerate(attributes.items()):
            if idx >= self._max_attributes:
                break
            norm_key = str(key)[: self._attribute_key_max_length]
            if isinstance(value, (int, float, bool)) or value is None:
                clean[norm_key] = value
            else:
                clean[norm_key] = str(value)[: self._attribute_value_max_length]
        return clean

    @staticmethod
    def _stable_hash(text: str) -> int:
        h = 2166136261
        for b in text.encode("utf-8"):
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    def _is_sampled_in(self, *, category: str, event: str, run_id: Optional[str], trace_id: Optional[str]) -> bool:
        rate = self._sample_overrides.get(f"{category}.{event}")
        if rate is None:
            rate = self._sample_overrides.get(category, self._default_sample_rate)
        if rate >= 1.0:
            return True
        if rate <= 0.0:
            return False
        seed = f"{category}|{event}|{run_id or ''}|{trace_id or ''}|{self._emit_counter}"
        bucket = self._stable_hash(seed) % 10000
        return bucket < int(rate * 10000)

    def _rate_limited(self, *, category: str, event: str, source: str) -> bool:
        now_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
        if now_key != self._rate_window_key:
            self._rate_window_key = now_key
            self._rate_counts = {}
        key = f"{source}:{category}:{event}"
        current = self._rate_counts.get(key, 0)
        if current >= self._per_key_rate_limit_per_minute:
            return True
        self._rate_counts[key] = current + 1
        return False

    @staticmethod
    def _latency_percentile(latencies: list[float], percentile: float) -> Optional[float]:
        if not latencies:
            return None
        ordered = sorted(latencies)
        rank = int(round((percentile / 100.0) * (len(ordered) - 1)))
        return float(ordered[max(min(rank, len(ordered) - 1), 0)])

    def _filtered_events(
        self,
        *,
        category: Optional[str] = None,
        event: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[ObservabilityEvent]:
        with self._lock:
            events = list(self._events)

        start_dt = self._parse_ts(start_time) if start_time else None
        end_dt = self._parse_ts(end_time) if end_time else None

        if category:
            events = [e for e in events if e.category == category]
        if event:
            events = [e for e in events if e.event == event]
        if run_id:
            events = [e for e in events if e.run_id == run_id]
        if status:
            events = [e for e in events if e.status == status]
        if source:
            events = [e for e in events if e.source == source]
        if start_dt:
            events = [
                e for e in events if (ts := self._parse_ts(e.timestamp)) is not None and ts >= start_dt
            ]
        if end_dt:
            events = [
                e for e in events if (ts := self._parse_ts(e.timestamp)) is not None and ts <= end_dt
            ]
        return events

    def emit(
        self,
        *,
        category: str,
        event: str,
        status: str = "info",
        run_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        source: str = "system",
        latency_ms: Optional[float] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Optional[ObservabilityEvent]:
        self._emit_counter += 1
        if not self._is_sampled_in(category=category, event=event, run_id=run_id, trace_id=trace_id):
            return None
        if self._rate_limited(category=category, event=event, source=source):
            return None

        safe_attributes = self._sanitize_attributes(attributes)
        payload = ObservabilityEvent(
            category=category,  # type: ignore[arg-type]
            event=event,
            status=status,  # type: ignore[arg-type]
            run_id=run_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
            source=source,  # type: ignore[arg-type]
            latency_ms=latency_ms,
            attributes=safe_attributes,
        )

        with self._lock:
            self._events.append(payload)

        metrics = get_metrics_collector()
        metrics.increment(
            "genxbot.observability.events",
            tags={"category": category, "event": event, "status": status, "source": source},
        )
        if latency_ms is not None:
            metrics.timing(
                "genxbot.observability.event_latency_seconds",
                latency_ms / 1000.0,
                tags={"category": category, "event": event},
            )

        add_event(
            f"genxbot.{event}",
            {
                "category": category,
                "status": status,
                "run_id": run_id or "",
                "trace_id": trace_id or "",
                "correlation_id": correlation_id or "",
                "source": source,
            },
        )
        return payload

    def list_events(
        self,
        *,
        limit: int = 100,
        category: Optional[str] = None,
        event: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[ObservabilityEvent]:
        events = self._filtered_events(
            category=category,
            event=event,
            run_id=run_id,
            status=status,
            source=source,
            start_time=start_time,
            end_time=end_time,
        )
        return events[-max(limit, 1) :]

    def page_events(
        self,
        *,
        limit: int = 100,
        cursor: Optional[str] = None,
        category: Optional[str] = None,
        event: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> ObservabilityEventsPage:
        filtered = self._filtered_events(
            category=category,
            event=event,
            run_id=run_id,
            status=status,
            source=source,
            start_time=start_time,
            end_time=end_time,
        )
        newest_first = list(reversed(filtered))
        total = len(newest_first)
        offset = 0
        if cursor:
            try:
                offset = max(int(cursor), 0)
            except ValueError:
                offset = 0
        lim = max(limit, 1)
        items = newest_first[offset : offset + lim]
        next_cursor = str(offset + lim) if (offset + lim) < total else None
        return ObservabilityEventsPage(items=items, total_filtered=total, next_cursor=next_cursor)

    def snapshot(
        self,
        *,
        category: Optional[str] = None,
        event: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> ObservabilitySnapshot:
        with self._lock:
            all_events = list(self._events)

        events = self._filtered_events(
            category=category,
            event=event,
            run_id=run_id,
            status=status,
            source=source,
            start_time=start_time,
            end_time=end_time,
        )

        by_category = Counter(e.category for e in events)
        by_event = Counter(e.event for e in events)
        by_status = Counter(e.status for e in events)
        latencies = [float(e.latency_ms) for e in events if e.latency_ms is not None]

        window_start = events[0].timestamp if events else None
        window_end = events[-1].timestamp if events else None

        return ObservabilitySnapshot(
            total_events=len(all_events),
            filtered_events=len(events),
            by_category=dict(by_category),
            by_event=dict(by_event),
            by_status=dict(by_status),
            latency_avg_ms=(sum(latencies) / len(latencies)) if latencies else None,
            latency_p50_ms=self._latency_percentile(latencies, 50.0),
            latency_p95_ms=self._latency_percentile(latencies, 95.0),
            window_start=window_start,
            window_end=window_end,
        )

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
