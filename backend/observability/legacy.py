"""Legacy lightweight observability helpers.

Provides ``Tracer`` and ``MetricsCollector`` classes kept for backward
compatibility. Newer code should use :mod:`backend.observability.tracing`
and :mod:`backend.observability.metrics` for full OpenTelemetry and
Prometheus support.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Span:
    """Represents a unit of work within a trace."""

    name: str
    start_time: float
    attributes: Dict[str, Any] = field(default_factory=dict)
    end_time: Optional[float] = None
    status: str = "unknown"

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000.0


class Tracer:
    """Manage spans for simple tracing."""

    def __init__(self) -> None:
        self._active: List[Span] = []
        self._finished: List[Span] = []

    def start_span(self, name: str, **attributes: Any) -> Span:
        span = Span(name=name, start_time=time.time(), attributes=dict(attributes))
        self._active.append(span)
        return span

    def end_span(self, span: Span, status: str = "ok") -> None:
        span.end_time = time.time()
        span.status = status
        try:
            self._active.remove(span)
        except ValueError:
            pass
        self._finished.append(span)

    def collect_finished(self) -> List[Span]:
        spans = self._finished[:]
        self._finished.clear()
        return spans


class MetricsCollector:
    """Collect and aggregate numerical metrics."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Dict[str, float]] = {}

    def record(self, name: str, value: float) -> None:
        entry = self._metrics.setdefault(
            name, {"count": 0, "sum": 0.0, "min": value, "max": value}
        )
        entry["count"] += 1
        entry["sum"] += value
        if value < entry["min"]:
            entry["min"] = value
        if value > entry["max"]:
            entry["max"] = value

    def start_timer(self, name: str) -> float:
        return time.time()

    def stop_timer(self, name: str, start_time: float) -> None:
        elapsed = (time.time() - start_time) * 1000.0
        self.record(name, elapsed)

    def summary(self) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for name, entry in self._metrics.items():
            count = entry["count"]
            total = entry["sum"]
            min_val = entry["min"]
            max_val = entry["max"]
            avg = total / count if count > 0 else 0.0
            summary[name] = {
                "count": float(count),
                "sum": total,
                "min": min_val,
                "max": max_val,
                "avg": avg,
            }
        return summary


__all__ = ["Tracer", "Span", "MetricsCollector"]

