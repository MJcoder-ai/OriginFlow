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


# -----------------------------------------------------------------------------
# Below are additional schemas introduced to support the enhanced agentic
# pipeline and chat UI.  These models define the structure of high-level
# planning tasks, rich card content and quick actions that the backend can
# return to the frontend.  They are purely descriptive and do not contain
# behaviour.  By centralising these definitions here we ensure a single
# source of truth between the API and the frontend store.

class PlanTaskStatus(str, Enum):
    """Enumeration of possible states for a planning task.

    A task begins in the ``pending`` state and transitions to ``in_progress``
    when the orchestrator has started work on it.  Upon successful
    completion it enters the ``complete`` state.  If a task cannot proceed
    because of unmet dependencies or external requirements it should be
    marked ``blocked``.  The frontend uses these statuses to display
    progress indicators in the plan timeline.
    """

    pending = "pending"
    in_progress = "in_progress"
    complete = "complete"
    blocked = "blocked"


class PlanTask(BaseModel):
    """Model representing a single high-level task in the AI's plan.

    Attributes:
        id: A unique identifier for this task.  Should remain stable
            throughout the task's lifetime.
        title: A succinct, user-friendly title describing the objective
            of the task (e.g. ``"Select panels"``).
        description: Optional longer description explaining the task in
            more detail.  This field may be omitted for simple tasks.
        status: Current execution status as a ``PlanTaskStatus``.
    """

    id: str
    title: str
    description: str | None = None
    status: PlanTaskStatus


class CardSpecItem(BaseModel):
    """A key/value pair describing a specification in a design card."""

    label: str
    value: str


class CardAction(BaseModel):
    """Represents an interactive action associated with a design card.

    The ``label`` appears on a button in the UI and the ``command`` is
    sent back to the AI orchestrator when the user clicks the button.
    """

    label: str
    command: str


class DesignCard(BaseModel):
    """Structured representation of rich content returned by agents.

    A card aggregates a title, optional description, an image URL, a list
    of specifications and a set of actions.  The frontend uses this
    structure to render visually rich messages in the chat sidebar.
    """

    title: str
    description: str | None = None
    image_url: str | None = None
    specs: list[CardSpecItem] | None = None
    actions: list[CardAction] | None = None


class QuickAction(BaseModel):
    """A short one-click command suggested by the AI.

    Quick actions appear beneath the chat input to enable rapid
    continuation of the conversation.  Each quick action carries a unique
    identifier for tracking, a human-readable label, and a command string
    that is sent back to the AI when triggered.
    """

    id: str
    label: str
    command: str


class PlanResponse(BaseModel):
    """Response model for the /ai/plan endpoint.

    Contains an ordered list of planning tasks and an optional list of
    quick actions suggested by the orchestrator.  This model can be
    extended in future to include additional metadata such as progress
    summaries or recommended modes.
    """

    tasks: list[PlanTask]
    quick_actions: list[QuickAction] | None = None


# --- NEW ---------------------------------------------------------
class AiCommandRequest(BaseModel):
    """Request body for AI command endpoints."""

    command: str
    requirements: dict | None = None


class AnalyzeCommandRequest(BaseModel):
    """Body for /ai/analyze-design."""

    command: str
    snapshot: DesignSnapshot


AnalyzeCommandRequest.model_rebuild()
# ----------------------------------------------------------------
