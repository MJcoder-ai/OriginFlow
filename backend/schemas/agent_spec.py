from __future__ import annotations

from typing import List, Literal, Optional
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict


AllowedStatus = Literal["draft", "staged", "published", "archived"]


class AgentPattern(BaseModel):
    """
    A declarative trigger for the router. Either a plain keyword or a regex.
    """
    type: Literal["keyword", "regex"] = "keyword"
    value: str = Field(..., min_length=1, max_length=200)
    case_insensitive: bool = True

    @field_validator("value")
    @classmethod
    def _validate_regex_if_needed(cls, v: str, info):
        if info.data.get("type") == "regex":
            try:
                case_insensitive = info.data.get("case_insensitive", True)
                flags = re.IGNORECASE if case_insensitive else 0
                re.compile(v, flags)
            except re.error as e:
                raise ValueError(f"Invalid regex: {e}") from e
        return v


class AgentCapability(BaseModel):
    """
    Describes a single capability/action exposed by the agent.
    e.g., {"action": "add_component", "schema": {...}} where schema is
    a JSON schema (or lightweight descriptor) for payload validation.
    Internally stored as ``spec`` but exposed as ``schema`` for backward
    compatibility.
    """
    action: str = Field(..., min_length=2, max_length=64)
    description: Optional[str] = Field(None, max_length=300)
    spec: Optional[dict] = Field(None, alias="schema")
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, populate_by_name=True
    )

    def to_api(self) -> dict:
        """Serialize capability for external APIs using aliases."""
        return self.model_dump(by_alias=True)


class AgentSpecModel(BaseModel):
    """
    Pydantic (v2) validation model for agent specs stored in DB.
    Mirrors, but does not replace, the in-memory dataclass used by the runtime
    registry.
    """
    name: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]+$"
    )
    display_name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    domain: Optional[str] = Field(None, max_length=64)
    risk_class: Optional[str] = Field(None, max_length=32)
    patterns: List[AgentPattern] = Field(default_factory=list)
    llm_tools: List[str] = Field(
        default_factory=list
    )  # declared tool names, resolved at runtime
    capabilities: List[AgentCapability] = Field(default_factory=list)
    config: Optional[dict] = None

    @field_validator("llm_tools")
    @classmethod
    def _non_empty_tools(cls, v: list[str]):
        # Allow empty list, but if present ensure no empty strings
        if any((not t or not t.strip()) for t in v):
            raise ValueError("Tool names must be non-empty")
        return v

    @field_validator("patterns")
    @classmethod
    def _at_least_one_pattern(cls, v: list[AgentPattern]):
        if len(v) == 0:
            raise ValueError("At least one routing pattern is required")
        return v


class AgentDraftCreate(BaseModel):
    spec: AgentSpecModel


class AgentPublishRequest(BaseModel):
    version: Optional[int] = None  # if None, publish latest staged/draft
    # (auto-bump)
    notes: Optional[str] = None


class TenantAgentStateUpdate(BaseModel):
    enabled: Optional[bool] = None
    pinned_version: Optional[int] = None
    config_override: Optional[dict] = None


class AgentAssistSynthesizeRequest(BaseModel):
    idea: str = Field(..., min_length=10, max_length=4000)
    target_domain: Optional[str] = None
    target_actions: Optional[list[str]] = None


class AgentAssistRefineRequest(BaseModel):
    current_spec: AgentSpecModel
    critique: str = Field(..., min_length=5, max_length=4000)
