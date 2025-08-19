from __future__ import annotations

from typing import Literal, Optional, List

from pydantic import BaseModel, Field


ApprovalStatus = Literal["pending", "approved", "rejected", "applied"]


class ApprovalListQuery(BaseModel):
    status: Optional[ApprovalStatus] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ApprovalDecision(BaseModel):
    note: Optional[str] = Field(None, max_length=400)
    approve_and_apply: bool = False


class BatchDecisionItem(BaseModel):
    id: int
    approve: bool
    note: Optional[str] = None
    approve_and_apply: bool = False


class BatchDecisionRequest(BaseModel):
    items: List[BatchDecisionItem]

