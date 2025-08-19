from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, JSON, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class PendingAction(Base):
    """
    Queue of AI-proposed actions awaiting manual approval (or created when policy denies auto-approval).
    Status machine: pending -> approved|rejected -> applied (optional).
    """

    __tablename__ = "pending_actions"
    __table_args__ = (
        Index("ix_pending_actions_tenant_status", "tenant_id", "status"),
        Index("ix_pending_actions_session", "session_id"),
        Index("ix_pending_actions_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100))
    project_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected|applied
    reason: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)  # rejection reason or policy note
    requested_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    approved_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "payload": self.payload,
            "confidence": self.confidence,
            "status": self.status,
            "reason": self.reason,
            "requested_by_id": self.requested_by_id,
            "approved_by_id": self.approved_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }

