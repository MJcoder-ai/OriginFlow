"""Observability utilities.

The package now exposes Prometheus metrics helpers and optional
OpenTelemetry tracing while keeping lightweight ``Tracer`` and
``MetricsCollector`` classes for backward compatibility.
"""

from .legacy import Tracer, Span, MetricsCollector  # backward compat
from .tracing import init_tracing
from .metrics import METRICS_ENABLED

__all__ = ["Tracer", "Span", "MetricsCollector", "init_tracing", "METRICS_ENABLED"]
