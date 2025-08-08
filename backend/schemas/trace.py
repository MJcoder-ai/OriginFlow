"""Pydantic models for traceability APIs.

These schemas represent both individual trace events and aggregated
summaries of traces. A ``TraceEvent`` mirrors the ORM model while
``TraceSummary`` provides a condensed overview of a trace series for
listing endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TraceEvent(BaseModel):
    """Serialized representation of a single trace event."""

    id: int
    trace_id: str
    ts: datetime
    actor: str
    event_type: str
    payload: Dict[str, Any]
    sha256: Optional[str] = None
    prev_sha256: Optional[str] = None

    model_config = {"from_attributes": True}


class TraceSummary(BaseModel):
    """Aggregated overview of a trace series."""

    trace_id: str
    first_ts: datetime
    last_ts: datetime
    count: int
