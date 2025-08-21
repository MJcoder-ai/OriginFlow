"""API endpoints for accessing trace events and summaries.

These routes provide read‑only access to the trace table. Clients can
list all trace series and inspect individual trace events. Future
extensions may include exporting traces or streaming updates via
Server‑Sent Events or WebSocket.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.models.trace_event import TraceEvent as TraceEventModel
from backend.schemas.trace import TraceEvent as TraceEventSchema, TraceSummary


router = APIRouter()


@router.get("/traces", response_model=List[TraceSummary])
async def list_traces(session: AsyncSession = Depends(get_session)) -> List[TraceSummary]:
    """Return an aggregated list of all trace series.

    Groups events by ``trace_id`` and returns the first and last
    timestamps along with a count. This enables UIs to present an
    overview without loading the entire event payloads.
    """

    result = await session.execute(
        select(
            TraceEventModel.trace_id,
            func.min(TraceEventModel.ts),
            func.max(TraceEventModel.ts),
            func.count(TraceEventModel.id),
        ).group_by(TraceEventModel.trace_id)
    )
    rows = result.all()
    summaries: List[TraceSummary] = []
    for trace_id, first_ts, last_ts, count in rows:
        summaries.append(
            TraceSummary(
                trace_id=trace_id,
                first_ts=first_ts,
                last_ts=last_ts,
                count=count,
            )
        )
    return summaries


@router.get("/traces/{trace_id}", response_model=List[TraceEventSchema])
async def get_trace(
    trace_id: str, session: AsyncSession = Depends(get_session)
) -> List[TraceEventSchema]:
    """Return the full list of events for a given trace.

    Events are ordered chronologically by timestamp. If no events are
    found, an empty list is returned rather than a 404.
    """

    result = await session.execute(
        select(TraceEventModel).where(TraceEventModel.trace_id == trace_id).order_by(TraceEventModel.ts)
    )
    events = result.scalars().all()
    return [TraceEventSchema.model_validate(event) for event in events]
