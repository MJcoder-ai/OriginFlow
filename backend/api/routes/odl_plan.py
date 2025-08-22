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
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.planner.parser import parse_design_command
from backend.planner.schemas import AiPlan, AiPlanTask

logger = logging.getLogger(__name__)
router = APIRouter()


def classify_command_intent(command: str) -> Dict[str, any]:
    """
    Classify the user's intent and extract structured information.
    Returns a dict with intent, confidence, and extracted parameters.
    """
    lower = command.lower().strip()
    
    # Define command patterns with confidence scores
    patterns = {
        "add_component": {
            "patterns": [
                r"\b(add|create|insert|place)\s+(\d+\s+)?(panel|inverter|battery)",
                r"\b(add|create|insert|place)\s+(solar\s+)?(panel|inverter|battery)"
            ],
            "confidence": 0.9
        },
        "connect": {
            "patterns": [r"\b(connect|wire|link)\s+.+\s+to\s+"],
            "confidence": 0.85
        },
        "delete": {
            "patterns": [r"\b(delete|remove|clear|erase)\s+"],
            "confidence": 0.8
        },
        "arrange": {
            "patterns": [r"\b(arrange|layout|organize|position)"],
            "confidence": 0.7
        },
        "design": {
            "patterns": [r"\b(design|build|create)\s+.*\b(system|kw|watt)"],
            "confidence": 0.6
        }
    }
    
    best_match = {"intent": "unknown", "confidence": 0.0, "matches": []}
    
    for intent, config in patterns.items():
        for pattern in config["patterns"]:
            if re.search(pattern, lower):
                if config["confidence"] > best_match["confidence"]:
                    best_match = {
                        "intent": intent,
                        "confidence": config["confidence"],
                        "matches": [pattern]
                    }
                elif config["confidence"] == best_match["confidence"]:
                    best_match["matches"].append(pattern)
    
    return best_match


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
    logger.info(
        "Processing plan request: session=%s command='%s' layer=%s",
        session_id, command, layer
    )
    
    # Input validation
    if not command or not command.strip():
        logger.warning("Empty command received for session %s", session_id)
        return AiPlan(
            tasks=[],
            metadata={
                "session_id": session_id,
                "error": "Empty command",
                "raw": command,
            },
        )
    
    # Classify command intent for better understanding
    intent_info = classify_command_intent(command)
    logger.info(
        "Command classification: session=%s intent=%s confidence=%.2f",
        session_id, intent_info["intent"], intent_info["confidence"]
    )
    
    lower = command.lower().strip()
    chosen_layer = layer if layer in {"single-line", "electrical"} else None

    delete_re = re.compile(r"\b(delete|remove|clear|erase|wipe|reset)\b")
    panel_re = re.compile(r"\b(solar\s+)?panels?\b")
    inverter_re = re.compile(r"\b(inverters?|inv)\b")
    battery_re = re.compile(r"\b(batteries|battery|storage)\b")
    all_re = re.compile(r"\ball\b|everything|canvas|diagram")
    add_re = re.compile(r"\b(add|create|insert|place)\b")
    connect_re = re.compile(r"\b(connect|wire|link|attach|join)\b")
    to_re = re.compile(r"\bto\b")
    arrange_re = re.compile(r"\b(arrange|layout|organize|position)\b")
    move_re = re.compile(r"\b(move|drag|shift)\b")

    # Handle literal add commands (single component type)
    if add_re.search(lower):
        layer_name = chosen_layer or "single-line"
        
        # Extract quantity if specified
        quantity_match = re.search(r"\b(\d+)\b", command)
        count = int(quantity_match.group(1)) if quantity_match else 1
        
        if panel_re.search(lower) and not inverter_re.search(lower):
            logger.info("Recognized literal add panel command: session=%s count=%d", session_id, count)
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
                    "classification": intent_info,
                    "raw": command,
                },
            )
        
        if inverter_re.search(lower) and not panel_re.search(lower):
            logger.info("Recognized literal add inverter command: session=%s count=%d", session_id, count)
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

    # Handle literal connection commands
    if connect_re.search(lower) and to_re.search(lower):
        layer_name = chosen_layer or "single-line"
        
        # Parse connection patterns like "connect panel to inverter"
        if panel_re.search(lower) and inverter_re.search(lower):
            logger.info("Recognized panel-to-inverter connection command: session=%s", session_id)
            tasks = [
                AiPlanTask(
                    id="generate_wiring",
                    title="Connect panels to inverters",
                    description=f"Create connections between panels and inverters on the {layer_name} layer",
                    status="pending",
                    args={"layer": layer_name, "connection_type": "panel_to_inverter"},
                )
            ]
            return AiPlan(
                tasks=tasks,
                metadata={
                    "session_id": session_id,
                    "parsed": {"layer": layer_name, "source": "panel", "target": "inverter"},
                    "intent": "connect_literal",
                    "classification": intent_info,
                    "raw": command,
                },
            )
        
        # Generic connection command
        logger.info("Recognized generic connection command: session=%s", session_id)
        tasks = [
            AiPlanTask(
                id="generate_wiring",
                title="Generate connections",
                description=f"Auto-generate connections on the {layer_name} layer",
                status="pending",
                args={"layer": layer_name},
            )
        ]
        return AiPlan(
            tasks=tasks,
            metadata={
                "session_id": session_id,
                "parsed": {"layer": layer_name},
                "intent": "connect_generic",
                "raw": command,
            },
        )

    # Handle layout/arrangement commands
    if arrange_re.search(lower) or (lower.strip() in {"layout", "auto layout", "arrange"}):
        logger.info("Recognized layout/arrangement command: session=%s", session_id)
        layer_name = chosen_layer or "single-line"
        tasks = [
            AiPlanTask(
                id="auto_layout",
                title="Auto-arrange components",
                description=f"Automatically arrange components on the {layer_name} layer",
                status="pending",
                args={"layer": layer_name, "layout_type": "auto"},
            )
        ]
        return AiPlan(
            tasks=tasks,
            metadata={
                "session_id": session_id,
                "parsed": {"layer": layer_name},
                "intent": "arrange",
                "raw": command,
            },
        )

    # Fallback to design command parsing (creates full PV system)
    logger.info("Falling back to design command parsing: session=%s", session_id)
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
