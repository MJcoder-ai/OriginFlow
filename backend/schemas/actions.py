from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

# ---- Canonical, closed enums for tool-calls ----
ComponentClass = Literal[
    "panel", "inverter", "battery", "meter",
    "controller", "combiner", "optimizer", "disconnect"
]

class ActionRequest(BaseModel):
    """
    Canonical schema the AI must fill when deciding an action.
    Keep this small and stable so both LLM and deterministic code can emit it.
    """
    action: Literal["add_component","add_link","modify_property","delete","analyze","validate"]
    rationale: str = Field("", description="Short justification for audit/debug")
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    # Slots for add_component
    component_class: Optional[ComponentClass] = None
    component_model_id: Optional[str] = None  # chosen real library item (if any)
    quantity: Optional[int] = 1
    target_layer: Optional[Literal["single_line","high_level","civil","networking","physical"]] = "single_line"
    placement_hint: Optional[dict] = None  # e.g., {"near":"panel_1"} etc.

__all__ = ["ActionRequest", "ComponentClass"]
