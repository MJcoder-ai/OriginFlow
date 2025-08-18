"""In-memory metrics collection for OriginFlow.

This module defines :class:`MetricsService`, a lightweight recorder for
counters and latency measurements.  It keeps all data in-process and is
thread-safe, providing a minimal form of observability without external
dependencies.  For production deployments, integrate with a dedicated
metrics system such as Prometheus.
"""

from __future__ import annotations

import threading
from typing import Dict


class MetricsService:
    """Thread-safe metrics recorder."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._latency_sum: Dict[str, float] = {}
        self._latency_count: Dict[str, int] = {}

    def increment_counter(self, name: str, increment: int = 1) -> None:
        """Increment a named counter."""

        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + increment

    def record_latency(self, name: str, duration: float) -> None:
        """Record a latency sample for ``name`` in seconds."""

        with self._lock:
            self._latency_sum[name] = self._latency_sum.get(name, 0.0) + duration
            self._latency_count[name] = self._latency_count.get(name, 0) + 1

    def get_metrics(self) -> Dict[str, float]:
        """Return counters and average latencies as a flat dictionary."""

        with self._lock:
            metrics: Dict[str, float] = {}
            for name, value in self._counters.items():
                metrics[name] = float(value)
            for name, total in self._latency_sum.items():
                count = self._latency_count.get(name, 0)
                avg = total / count if count else 0.0
                metrics[f"{name}_avg"] = avg
            return metrics


# Global singleton used by the application
metrics = MetricsService()

