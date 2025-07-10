# backend/schemas/ai.py
"""Schemas for AI command parsing and actions."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel


class AiActionType(str, Enum):
    """Supported actions produced by agents."""

    add_component = "addComponent"
    remove_component = "removeComponent"
    add_link = "addLink"
    remove_link = "removeLink"
    update_position = "updatePosition"


class AiAction(BaseModel):
    """Validated action emitted by an AI agent."""

    action: AiActionType
    payload: Dict[str, Any]
    version: int

# --- NEW ---------------------------------------------------------
class AiCommandRequest(BaseModel):
    """Request body for /api/v1/ai/command."""

    command: str
# ----------------------------------------------------------------
