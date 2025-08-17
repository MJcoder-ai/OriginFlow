"""Pydantic models for memory management APIs.

This module defines the ``Memory`` schema used by the `/memory` API.
The schema mirrors the fields defined on the ``Memory`` ORM model to
expose persisted memories via FastAPI while enforcing type safety.  When
the ORM model is extended with new fields, update this schema
accordingly and regenerate the frontend TypeScript definitions to avoid
misalignment:contentReference[oaicite:4]{index=4}.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class Memory(BaseModel):
    """Serialized view of a memory entry."""

    id: int
    tenant_id: str
    project_id: Optional[str] = None
    kind: str
    created_at: datetime
    tags: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    sha256: Optional[str] = None
    prev_sha256: Optional[str] = None

    model_config = {"from_attributes": True}
