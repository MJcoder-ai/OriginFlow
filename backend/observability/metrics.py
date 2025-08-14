"""Simple metrics collection utilities.

The ``MetricsCollector`` class provides a lightweight mechanism for
recording and summarising quantitative observations during
execution.  Each metric is identified by a string name.  Metrics
can be recorded either as discrete values (via ``record``) or as
timings (via ``start_timer``/``stop_timer``).  For each metric the
collector maintains the number of samples, the sum of the values,
the minimum and maximum recorded value, and computes the average
upon summarisation.

This implementation is intentionally minimalist: it does not
support histograms, percentiles or exporting to external
monitoring systems.  Future iterations may integrate with
OpenTelemetry or other observability backends.
"""
from __future__ import annotations

import time
from typing import Dict, Optional


class MetricsCollector:
    """Collect and aggregate numerical metrics.

    The collector stores metrics in an internal dictionary keyed by
    metric name.  Each entry is a dictionary with keys ``count``,
    ``sum``, ``min`` and ``max``.  The ``record`` method
    increments the count and updates the sum, minimum and maximum
    observed values.  Timings can be recorded using ``start_timer``
    and ``stop_timer`` which compute the elapsed time between
    invocations.
    """

    def __init__(self) -> None:
        # Each metric name maps to a dict with keys: count, sum, min, max.
        self._metrics: Dict[str, Dict[str, float]] = {}

    def record(self, name: str, value: float) -> None:
        """Record a numeric value for the given metric.

        Args:
            name: The name of the metric.
            value: The numeric value to record.
        """
        entry = self._metrics.setdefault(
            name, {"count": 0, "sum": 0.0, "min": value, "max": value}
        )
        entry["count"] += 1
        entry["sum"] += value
        # Update min and max
        if value < entry["min"]:
            entry["min"] = value
        if value > entry["max"]:
            entry["max"] = value

    def start_timer(self, name: str) -> float:
        """Start timing a metric.

        Returns:
            A floating‑point timestamp that should be passed to
            ``stop_timer`` to compute the elapsed time.
        """
        return time.time()

    def stop_timer(self, name: str, start_time: float) -> None:
        """Stop a timer and record the elapsed time.

        Args:
            name: The name of the metric for timing.
            start_time: The timestamp returned by ``start_timer``.
        """
        elapsed = (time.time() - start_time) * 1000.0  # milliseconds
        self.record(name, elapsed)

    def summary(self) -> Dict[str, Dict[str, float]]:
        """Return a summary of all recorded metrics.

        For each metric returns a dictionary containing the count,
        sum, min, max and average values.

        Returns:
            A mapping from metric names to summary statistics.
        """
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
