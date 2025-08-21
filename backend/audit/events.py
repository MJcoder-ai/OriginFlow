"""
Audit event log – append-only.

This module defines a small table and a helper to log audit events such as:
 - patch_proposed, patch_approved, patch_applied, patch_rejected
"""
from __future__ import annotations

from typing import Dict
from datetime import datetime, timezone
from sqlalchemy import Table, Column, String, JSON, MetaData, DateTime, insert
from sqlalchemy.orm import Session

metadata = MetaData()

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("session_id", String, nullable=False),
    Column("type", String, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False),
)


def init_audit(db: Session) -> None:
    engine = db.get_bind()
    metadata.create_all(engine)


def log_event(db: Session, *, id: str, session_id: str, type: str, payload: Dict) -> None:
    now = datetime.now(timezone.utc)
    db.execute(
        insert(audit_events).values(
            id=id, session_id=session_id, type=type, payload=payload, created_at=now
        )
    )
    db.commit()
