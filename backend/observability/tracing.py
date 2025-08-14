"""Lightweight tracing utilities.

The ``Tracer`` and ``Span`` classes provide minimal instrumentation for
recording execution spans.  Each span captures its name, start and end
times, a status and arbitrary key‑value attributes.  Finished spans can
be collected for reporting or further processing.

This module intentionally avoids external dependencies and is suitable
for unit tests or local development.  It can be extended or replaced
with a full OpenTelemetry implementation in the future.
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
        """Return the duration of the span in milliseconds."""
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
