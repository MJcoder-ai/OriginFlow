"""
Minimal session scratchpad (memory).

Stores compact structured context (requirements, last decisions). This is not a
chat log. Use to keep small, durable signals that improve orchestration.
"""
from __future__ import annotations

from typing import Dict, Optional
from sqlalchemy import Table, Column, String, JSON, MetaData, insert, update, select
from sqlalchemy.orm import Session

metadata = MetaData()

session_memory = Table(
    "session_memory",
    metadata,
    Column("session_id", String, primary_key=True),
    Column("data", JSON, nullable=False),
)


def init_memory(db: Session) -> None:
    engine = db.get_bind()
    metadata.create_all(engine)


def get(db: Session, session_id: str) -> Optional[Dict]:
    row = db.execute(select(session_memory).where(session_memory.c.session_id == session_id)).fetchone()
    if not row:
        return None
    return dict(row._mapping)["data"]


def set(db: Session, session_id: str, data: Dict) -> None:
    if get(db, session_id) is None:
        db.execute(insert(session_memory).values(session_id=session_id, data=data))
    else:
        db.execute(update(session_memory).where(session_memory.c.session_id == session_id).values(data=data))
    db.commit()
