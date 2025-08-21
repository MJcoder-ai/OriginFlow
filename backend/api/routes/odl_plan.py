"""
Server-side planner endpoint (clean architecture).

Exposes:
  GET /api/v1/odl/sessions/{session_id}/plan?command=...

Returns an AiPlan containing a small set of deterministic tasks that the
frontend can execute via /odl/sessions/{sid}/act (vNext flow). The planner
is intentionally rule-based for MVP reliability; it parses key quantities
from natural language (e.g., "design a 5kW ...") and emits typed tasks.
"""
from fastapi import APIRouter, Query, Path, Depends
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.planner.parser import parse_design_command
from backend.planner.schemas import AiPlan, AiPlanTask

router = APIRouter()


@router.get("/odl/sessions/{session_id}/plan", response_model=AiPlan, tags=["planner"])
async def get_plan_for_session(
    session_id: str = Path(..., description="ODL session id"),
    command: str = Query(..., description="Natural language design request"),
    db: AsyncSession = Depends(get_session),
) -> AiPlan:
    """
    Build a deterministic plan from the user's natural language command.

    Notes:
    - We do *not* execute any changes here; the client will call /act for each task.
    - This endpoint is safe to call even if the session is empty; tools will
      validate preconditions when executed.
    """
    plan = parse_design_command(command)

    # Enforce consistent args for vNext tools.
    # Emit two placeholder tasks (inverter, panels) followed by wiring.
    tasks: List[AiPlanTask] = [
        AiPlanTask(
            id="make_placeholders",
            title="Create inverter",
            description="Add one inverter placeholder on the electrical layer",
            status="pending",
            args={"component_type": "inverter", "count": 1, "layer": plan.layer},
        ),
        AiPlanTask(
            id="make_placeholders",
            title=f"Create {plan.panel_count} panels",
            description=f"Add {plan.panel_count} panel placeholders (≈{plan.panel_watts} W per panel) on the {plan.layer} layer",
            status="pending",
            args={"component_type": "panel", "count": plan.panel_count, "layer": plan.layer},
        ),
        AiPlanTask(
            id="generate_wiring",
            title="Generate wiring",
            description=f"Auto-generate connections on {plan.layer}",
            status="pending",
            args={"layer": plan.layer},
        ),
    ]

    return AiPlan(
        tasks=tasks,
        metadata={
            "session_id": session_id,
            "parsed": {
                "target_kw": plan.target_kw,
                "panel_watts": plan.panel_watts,
                "layer": plan.layer,
            },
            "assumptions": plan.assumptions,
        },
    )
