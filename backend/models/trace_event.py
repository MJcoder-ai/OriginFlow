"""ORM model for request/response trace events.

Each ``TraceEvent`` record represents a single atomic operation or
decision made by the OriginFlow platform. Events are grouped by a
common ``trace_id`` and ordered chronologically via the ``ts`` column.
Storing payloads as JSON enables full auditability of user inputs,
intermediate AI agent calls and resulting actions. The optional
cryptographic hashes (``sha256`` and ``prev_sha256``) allow a
tamper‑evident chain of events to be verified externally.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class TraceEvent(Base):
    """Persistent timeline event for auditing and compliance."""

    __tablename__ = "trace_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actor: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    prev_sha256: Mapped[str | None] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TraceEvent(id={self.id}, trace_id={self.trace_id}, actor={self.actor}, "
            f"event_type={self.event_type}, ts={self.ts})"
        )
