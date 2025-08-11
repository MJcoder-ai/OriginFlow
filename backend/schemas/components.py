"""Schemas for component ingestion."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class ComponentIngestRequest(BaseModel):
    category: str
    part_number: str
    attributes: Dict[str, Any]


class ComponentIngestResponse(BaseModel):
    component_id: str
