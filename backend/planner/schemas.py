from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ParsedPlan(BaseModel):
    """
    Parsed quantities / assumptions extracted from the NL command.
    """
    target_kw: float = Field(..., description="Target DC power in kW")
    panel_watts: int = Field(..., description="Assumed panel wattage used for sizing")
    panel_count: int = Field(..., description="Computed number of panels")
    layer: str = Field("electrical", description="Target design layer (e.g., electrical, single-line)")
    assumptions: Dict[str, Any] = Field(default_factory=dict)


class AiPlanTask(BaseModel):
    """
    One deterministic step the client can execute via /odl/sessions/{sid}/act.
    """
    id: str = Field(..., description="Task identifier (e.g., make_placeholders, generate_wiring)")
    title: str
    description: Optional[str] = None
    status: str = Field("pending", description="pending | in_progress | complete | blocked")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to /act")


class AiPlan(BaseModel):
    """
    Planner response compatible with the frontend's plan UI.
    """
    tasks: List[AiPlanTask]
    metadata: Dict[str, Any] = Field(default_factory=dict)
