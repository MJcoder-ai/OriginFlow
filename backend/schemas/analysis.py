from __future__ import annotations

from typing import List
from pydantic import BaseModel


class CanvasComponent(BaseModel):
    id: str
    name: str
    type: str
    standard_code: str
    x: int
    y: int


class CanvasLink(BaseModel):
    id: str
    source_id: str
    target_id: str


class DesignSnapshot(BaseModel):
    components: List[CanvasComponent]
    links: List[CanvasLink]


DesignSnapshot.model_rebuild()
