"""Pydantic models for memory management APIs.

These schemas define the shape of data returned by the memory API. The
``Memory`` class mirrors the ORM model to expose memory entries via
FastAPI routes while enforcing types at runtime. Optional fields
such as ``project_id`` and ``tags`` are represented with ``None``
defaults.
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
