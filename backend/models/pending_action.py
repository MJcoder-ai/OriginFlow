from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Float, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class PendingAction(Base):
    """Queue of AI-proposed actions awaiting manual approval."""

    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    agent_name: Mapped[str] = mapped_column(String(100))
    action_type: Mapped[str] = mapped_column(String(100))
    risk_class: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


Index(
    "ix_pending_actions_tenant_status_created",
    PendingAction.tenant_id,
    PendingAction.status,
    PendingAction.created_at,
)

