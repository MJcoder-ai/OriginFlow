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
from typing import Dict, List, Optional
import re

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.planner.parser import parse_design_command
from backend.planner.schemas import AiPlan, AiPlanTask

router = APIRouter()


@router.get("/odl/sessions/{session_id}/plan", response_model=AiPlan, tags=["planner"])
async def get_plan_for_session(
    session_id: str = Path(..., description="ODL session id"),
    command: str = Query(..., description="Natural language design request"),
    layer: Optional[str] = Query(
        None, description="Target layer override (e.g., 'single-line' or 'electrical')"
    ),
    db: AsyncSession = Depends(get_session),
) -> AiPlan:
    """
    Build a deterministic plan from the user's natural language command.

    Notes:
    - We do *not* execute any changes here; the client will call /act for each task.
    - This endpoint is safe to call even if the session is empty; tools will
      validate preconditions when executed.
    """
    lower = command.lower()
    chosen_layer = layer if layer in {"single-line", "electrical"} else None

    delete_re = re.compile(r"\b(delete|remove|clear|erase|wipe|reset)\b")
    panel_re = re.compile(r"\b(solar\s+)?panels?\b")
    inverter_re = re.compile(r"\b(inverters?|inv)\b")
    battery_re = re.compile(r"\b(batteries|battery|storage)\b")
    all_re = re.compile(r"\ball\b|everything|canvas|diagram")
    add_re = re.compile(r"\b(add|create|insert|place)\b")

    # Handle literal add commands (single component type)
    if add_re.search(lower):
        layer_name = chosen_layer or "single-line"
        
        # Extract quantity if specified
        quantity_match = re.search(r"\b(\d+)\b", command)
        count = int(quantity_match.group(1)) if quantity_match else 1
        
        if panel_re.search(lower) and not inverter_re.search(lower):
            tasks = [
                AiPlanTask(
                    id="make_placeholders",
                    title=f"Add {count} solar panel{'s' if count != 1 else ''}",
                    description=f"Add {count} panel placeholder{'s' if count != 1 else ''} on the {layer_name} layer",
                    status="pending",
                    args={"component_type": "panel", "count": count, "layer": layer_name},
                )
            ]
            return AiPlan(
                tasks=tasks,
                metadata={
                    "session_id": session_id,
                    "parsed": {"layer": layer_name, "component": "panel", "count": count},
                    "intent": "add_literal",
                    "raw": command,
                },
            )
        
        if inverter_re.search(lower) and not panel_re.search(lower):
            tasks = [
                AiPlanTask(
                    id="make_placeholders",
                    title=f"Add {count} inverter{'s' if count != 1 else ''}",
                    description=f"Add {count} inverter placeholder{'s' if count != 1 else ''} on the {layer_name} layer",
                    status="pending",
                    args={"component_type": "inverter", "count": count, "layer": layer_name},
                )
            ]
            return AiPlan(
                tasks=tasks,
                metadata={
                    "session_id": session_id,
                    "parsed": {"layer": layer_name, "component": "inverter", "count": count},
                    "intent": "add_literal",
                    "raw": command,
                },
            )
        
        if battery_re.search(lower):
            tasks = [
                AiPlanTask(
                    id="make_placeholders",
                    title=f"Add {count} battery{'ies' if count != 1 else 'y'}",
                    description=f"Add {count} battery placeholder{'s' if count != 1 else ''} on the {layer_name} layer",
                    status="pending",
                    args={"component_type": "battery", "count": count, "layer": layer_name},
                )
            ]
            return AiPlan(
                tasks=tasks,
                metadata={
                    "session_id": session_id,
                    "parsed": {"layer": layer_name, "component": "battery", "count": count},
                    "intent": "add_literal", 
                    "raw": command,
                },
            )

    if delete_re.search(lower) and panel_re.search(lower):
        layer_name = chosen_layer or "single-line"
        tasks = [
            AiPlanTask(
                id="delete_nodes",
                title="Delete all panels",
                description=f"Remove all panel placeholders on the {layer_name} layer",
                status="pending",
                args={
                    "component_types": ["panel", "pv_module", "solar_panel", "generic_panel"],
                    "layer": layer_name,
                },
            )
        ]
        return AiPlan(
            tasks=tasks,
            metadata={
                "session_id": session_id,
                "parsed": {"layer": layer_name},
                "intent": "delete_panels",
                "raw": command,
            },
        )

    if delete_re.search(lower) and (all_re.search(lower) or lower.strip() in {"delete", "reset", "clear"}):
        layer_name = chosen_layer or "single-line"
        tasks = [
            AiPlanTask(
                id="delete_nodes",
                title="Clear canvas",
                description=f"Remove all nodes on the {layer_name} layer",
                status="pending",
                args={"component_types": ["*"], "layer": layer_name},
            )
        ]
        return AiPlan(
            tasks=tasks,
            metadata={
                "session_id": session_id,
                "parsed": {"layer": layer_name},
                "intent": "clear_canvas",
                "raw": command,
            },
        )

    plan = parse_design_command(command)
    if chosen_layer:
        plan.layer = chosen_layer

    tasks: List[AiPlanTask] = [
        AiPlanTask(
            id="make_placeholders",
            title="Create inverter",
            description=f"Add one inverter placeholder on the {plan.layer} layer",
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
