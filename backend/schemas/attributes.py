from __future__ import annotations
from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field

class SourceRef(BaseModel):
    file_id: str
    page: Optional[int] = None
    bbox: Optional[list[float]] = None

class ValueVersion(BaseModel):
    value_id: Optional[str] = None
    value: Any
    unit: Optional[str] = None
    version: Optional[int] = None
    is_verified: bool = False
    confidence: Optional[float] = None
    source: Optional[SourceRef] = None

class AttributeViewItem(BaseModel):
    attribute_id: str
    display_label: str
    key: str
    category: Optional[str] = "General"
    data_type: Literal["string","number","integer","boolean","enum","date","json"] = "string"
    cardinality: Literal["one","many"] = "one"
    unit_default: Optional[str] = None
    applicable: bool = True

    current: Optional[ValueVersion] = None
    candidates: List[ValueVersion] = Field(default_factory=list)
    history_count: int = 0

class AttributePatch(BaseModel):
    attribute_id: str
    op: Literal["upsert","delete","verify"] = "upsert"
    value: Optional[Any] = None
    unit: Optional[str] = None
    mark_verified: bool = False
    group_id: Optional[str] = None
    rank: Optional[int] = None
    source_id: Optional[str] = None

class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None
    trace_id: Optional[str] = None
