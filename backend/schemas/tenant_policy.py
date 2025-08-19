from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional

class PolicyDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_approve_enabled: bool = True
    risk_threshold_default: float = Field(0.80, ge=0.0, le=1.0)
    action_whitelist: Dict[str, List[str]] = Field(default_factory=lambda: {"actions": []})
    action_blacklist: Dict[str, List[str]] = Field(default_factory=lambda: {"actions": []})
    enabled_domains: Dict[str, List[str]] = Field(default_factory=lambda: {"domains": []})
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1

    @field_validator("action_whitelist", "action_blacklist")
    @classmethod
    def _validate_actions(cls, v):
        actions = v.get("actions", [])
        if not isinstance(actions, list) or not all(isinstance(x, str) and x for x in actions):
            raise ValueError("actions must be a non-empty list of strings or empty list")
        return {"actions": actions}

    @field_validator("enabled_domains")
    @classmethod
    def _validate_domains(cls, v):
        domains = v.get("domains", [])
        if not isinstance(domains, list) or not all(isinstance(x, str) and x for x in domains):
            raise ValueError("domains must be a list of strings")
        return {"domains": domains}

class PolicyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Partial update (PATCH-like), but must include version for optimistic concurrency.
    auto_approve_enabled: Optional[bool] = None
    risk_threshold_default: Optional[float] = Field(None, ge=0.0, le=1.0)
    action_whitelist: Optional[Dict[str, List[str]]] = None
    action_blacklist: Optional[Dict[str, List[str]]] = None
    enabled_domains: Optional[Dict[str, List[str]]] = None
    feature_flags: Optional[Dict[str, bool]] = None
    data: Optional[Dict[str, Any]] = None
    version: int

class PolicyTestRequest(BaseModel):
    action_type: str
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    agent_name: str | None = None

class PolicyTestResult(BaseModel):
    auto_approved: bool
    reason: str
    threshold_used: float
    matched_rule: str | None = None
