"""
Utilities for capturing metrics and tracing execution spans.

This module provides simple helper functions to measure execution time and
record arbitrary metrics for later analysis.  While a full telemetry stack
such as OpenTelemetry is recommended for production, these helpers
introduce minimal overhead and integrate with Python's logging facility.

Usage:

    from backend.utils.observability import trace_span, record_metric

    with trace_span("validate_actions", task_count=len(actions)):
        # do some work
        record_metric("action_processed", 1, {"agent": agent_name})

Each call to ``trace_span`` logs the elapsed wall‑clock time in
milliseconds upon exit, along with the provided contextual tags.  Metrics
recorded via ``record_metric`` are logged immediately, enabling
aggregation via log processors or external systems.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterable

_logger = logging.getLogger("originflow.observability")


def record_metric(name: str, value: float, tags: Dict[str, Any] | None = None) -> None:
    """Log a metric with an associated value and optional tags.

    Metrics are logged using the ``originflow.observability`` logger.  They
    can be shipped to a metrics backend via a log exporter or scraped from
    the logs by an external pipeline.  Tags should be simple serialisable
    values (strings, numbers) to avoid JSON serialisation issues.

    Args:
        name: Identifier of the metric (e.g. ``actions_processed``).
        value: Numeric value to record.
        tags: Optional dictionary of key–value pairs describing the context.
    """
    _logger.info(
        "metric.%s value=%s tags=%s",
        name,
        value,
        tags or {},
    )


@contextmanager
def trace_span(name: str, **context: Any) -> Iterable[None]:
    """Context manager that measures execution time and logs the result.

    When the context block exits, the elapsed time is computed and logged
    as both a metric and a human‑readable message.  The ``name`` should
    identify the operation being measured, and ``context`` may include
    arbitrary metadata (such as agent names or task identifiers).

    Args:
        name: Name of the span (e.g. ``agent_run``).
        **context: Arbitrary key–value pairs for additional context.

    Yields:
        None – the managed context.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000.0
        # Log a span event with the duration and context for human readers.
        _logger.info(
            "span.%s duration_ms=%.2f context=%s",
            name,
            duration_ms,
            context,
        )
        # Also record a metric for machine consumption.
        record_metric(f"{name}.duration_ms", duration_ms, context)

