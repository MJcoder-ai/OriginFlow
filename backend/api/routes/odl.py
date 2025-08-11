"""ODL graph and planning routes."""
from __future__ import annotations

from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.schemas.ai import AiCommandRequest, PlanTask
from backend.schemas.odl import ActOnTaskRequest, CreateSessionResponse, CreateSessionRequest, GraphResponse
from backend.agents.planner_agent import PlannerAgent
from backend.agents.registry import registry
from backend.services import odl_graph_service

router = APIRouter(prefix="/odl", tags=["odl"])

planner_agent = PlannerAgent()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(cmd: CreateSessionRequest | None = None) -> CreateSessionResponse:
    """Create a new design session and initialise its graph.

    Accepts an optional body; when a `session_id` is provided by the
    frontend, reuse it to allow stable sessions across refreshes.
    """
    # Prefer client-provided id when present
    provided_session_id = None
    provided_session_id = getattr(cmd, "session_id", None) if cmd else None
    session_id = provided_session_id or str(uuid4())
    odl_graph_service.create_graph(session_id)
    return CreateSessionResponse(session_id=session_id)


@router.post("/{session_id}/plan", response_model=List[PlanTask])
async def get_plan(session_id: str, cmd: AiCommandRequest) -> List[PlanTask]:
    """
    Return a dynamic list of tasks for this session.  The request may
    include partial requirements (target power, roof area, budget) which are
    saved on the graph.  The planner then inspects the graph and user
    inputs to determine which tasks are needed.
    """
    requirements = getattr(cmd, "requirements", None)
    if requirements:
        graph = await odl_graph_service.get_graph(session_id)
        graph.graph.setdefault("requirements", {}).update(requirements)
        await odl_graph_service.save_graph(session_id, graph)
    tasks = await planner_agent.plan(session_id, cmd.command, requirements=requirements)
    return [PlanTask(**t) for t in tasks]


@router.post("/{session_id}/act", response_model=GraphResponse)
async def act_on_task(session_id: str, req: ActOnTaskRequest) -> GraphResponse:
    """Execute a task on the current graph."""
    task_id = req.task_id.lower().strip()
    agent = registry.get_agent(task_id)
    if agent:
        result = await agent.execute(session_id, task_id)
    else:
        result = {
            "card": {"title": "Unknown task", "body": f"Task {req.task_id} not supported."},
            "patch": None,
            "status": "error",
        }
    patch = result.get("patch")
    if patch:
        graph = await odl_graph_service.get_graph(session_id)
        patch_with_version = dict(patch)
        # Prefer client-observed version for optimistic concurrency if provided
        client_version = req.graph_version
        patch_with_version["version"] = (
            client_version if client_version is not None else graph.graph.get("version", 0)
        )
        success, error = await odl_graph_service.apply_patch(session_id, patch_with_version)
        if not success:
            raise HTTPException(status_code=409, detail=error)
        # Load updated version to return
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    else:
        graph = await odl_graph_service.get_graph(session_id)
        current_version = graph.graph.get("version", None)
    return GraphResponse(
        card=result["card"],
        patch=patch,
        status=result.get("status", "pending"),
        version=current_version,
    )
