"""Utility functions for emitting trace events.

The tracing service provides helpers to start new trace series and
record individual events into the ``trace_event`` table. Each event
optionally links to a previous event via a cryptographic hash,
enabling tamper detection. While not yet integrated into the
orchestrator, these functions establish the pattern for future
instrumentation.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.trace_event import TraceEvent


async def start_trace() -> str:
    """Generate a new random trace identifier.

    A trace ID groups together all events belonging to the same
    interaction or workflow. This helper simply returns a UUID4
    string. Persisting the trace itself is implicit when the first
    event is emitted.
    """

    return str(uuid.uuid4())


async def emit_event(
    session: AsyncSession,
    trace_id: str,
    actor: str,
    event_type: str,
    payload: dict[str, Any],
    prev_sha: Optional[str] = None,
) -> TraceEvent:
    """Persist a single trace event and compute its hash.

    Args:
        session: Active async database session.
        trace_id: Identifier grouping this event with related ones.
        actor: Who generated the event, e.g. ``user`` or agent name.
        event_type: Short string describing the event kind.
        payload: Arbitrary JSON serializable content to store.
        prev_sha: Optional hash of the previous event for chaining.

    Returns:
        The persisted TraceEvent instance.
    """

    # Serialize payload deterministically for hashing
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    m = hashlib.sha256()
    if prev_sha:
        m.update(prev_sha.encode())
    m.update(data)
    sha256 = m.hexdigest()
    event = TraceEvent(
        trace_id=trace_id,
        actor=actor,
        event_type=event_type,
        payload=payload,
        sha256=sha256,
        prev_sha256=prev_sha,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event
