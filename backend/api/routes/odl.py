"""ODL graph and planning routes."""
from __future__ import annotations

from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.schemas.ai import AiCommandRequest, PlanTask
from backend.schemas.odl import (
    ActOnTaskRequest,
    CreateSessionResponse,
    GraphResponse,
)
from backend.agents.planner_agent import PlannerAgent
from backend.agents.odl_domain_agents import (
    PVDesignAgent,
    StructuralAgent,
    WiringAgent,
)
from backend.services import odl_graph_service

router = APIRouter(prefix="/odl", tags=["odl"])

planner_agent = PlannerAgent()
pv_agent = PVDesignAgent()
structural_agent = StructuralAgent()
wiring_agent = WiringAgent()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(cmd: AiCommandRequest) -> CreateSessionResponse:
    """Create a new design session and initialise its graph."""
    session_id = str(uuid4())
    odl_graph_service.create_graph(session_id)
    return CreateSessionResponse(session_id=session_id)


@router.post("/{session_id}/plan", response_model=List[PlanTask])
async def get_plan(session_id: str, cmd: AiCommandRequest) -> List[PlanTask]:
    """Return a list of tasks for this session."""
    tasks = await planner_agent.plan(session_id, cmd.command)
    return [PlanTask(**t) for t in tasks]


@router.post("/{session_id}/act", response_model=GraphResponse)
async def act_on_task(session_id: str, req: ActOnTaskRequest) -> GraphResponse:
    """Execute a task on the current graph."""
    task_id = req.task_id.lower().strip()
    if task_id in {"gather_requirements", "generate_design"}:
        result = await pv_agent.execute(session_id, task_id)
    elif task_id == "refine_validate":
        result = await structural_agent.execute(session_id, task_id)
    elif task_id == "generate_structural":
        result = await structural_agent.execute(session_id, task_id)
    elif task_id == "generate_wiring":
        result = await wiring_agent.execute(session_id, task_id)
    else:
        result = {
            "card": {
                "title": "Unknown task",
                "body": f"Task {req.task_id} not supported.",
            },
            "patch": None,
            "status": "error",
        }
    patch = result.get("patch")
    if patch:
        success, error = odl_graph_service.apply_patch(session_id, patch)
        if not success:
            raise HTTPException(status_code=400, detail=error)
    return GraphResponse(card=result["card"], patch=patch, status=result.get("status", "pending"))
