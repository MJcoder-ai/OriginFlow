# backend/schemas/ai.py
"""Schemas for AI command parsing and actions."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List

from .analysis import DesignSnapshot

from pydantic import BaseModel


class AiActionType(str, Enum):
    """Supported actions produced by agents."""

    add_component = "addComponent"
    remove_component = "removeComponent"
    add_link = "addLink"
    remove_link = "removeLink"
    update_position = "updatePosition"
    suggest_link = "suggestLink"
    validation = "validation"
    report = "report"


class PositionPayload(BaseModel):
    """Coordinates for a canvas component."""

    id: str
    x: int
    y: int


class BomReportPayload(BaseModel):
    """List of items returned by the BoM agent."""

    items: List[str]


class AiAction(BaseModel):
    """Validated action emitted by an AI agent."""

    action: AiActionType
    payload: Dict[str, Any]
    version: int
    confidence: float | None = None
    auto_approved: bool = False  # Whether this action was automatically approved by the learning system

# --- NEW ---------------------------------------------------------
class AiCommandRequest(BaseModel):
    """Request body for /api/v1/ai/command."""

    command: str


class AnalyzeCommandRequest(BaseModel):
    """Body for /ai/analyze-design."""

    command: str
    snapshot: DesignSnapshot


AnalyzeCommandRequest.model_rebuild()
# ----------------------------------------------------------------
