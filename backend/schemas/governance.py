from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class TenantSettingsRead(BaseModel):
    tenant_id: str
    ai_auto_approve: bool
    risk_threshold_low: float
    risk_threshold_medium: float
    risk_threshold_high: float
    whitelisted_actions: dict | None = None
    enabled_domains: dict | None = None
    feature_flags: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantSettingsUpdate(BaseModel):
    ai_auto_approve: Optional[bool] = None
    risk_threshold_low: Optional[float] = Field(None, ge=0.0)
    risk_threshold_medium: Optional[float] = Field(None, ge=0.0)
    risk_threshold_high: Optional[float] = Field(None, ge=0.0)
    whitelisted_actions: Optional[dict] = None
    enabled_domains: Optional[dict] = None
    feature_flags: Optional[dict] = None


class PendingActionRead(BaseModel):
    id: int
    tenant_id: str
    project_id: str | None
    session_id: str | None
    trace_id: str | None
    agent_name: str
    action_type: str
    risk_class: str
    confidence: float
    payload: dict
    status: Literal["pending", "approved", "rejected"]
    created_by: str | None
    decided_by: str | None
    decision_reason: str | None
    created_at: datetime
    decided_at: datetime | None

    class Config:
        from_attributes = True


class PendingActionDecision(BaseModel):
    reason: Optional[str] = None

