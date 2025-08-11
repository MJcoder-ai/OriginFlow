"""ODL Graph and Planning API routes.

This FastAPI router exposes endpoints for interacting with the
OriginFlow Design Language (ODL) graphs and for generating
high-level plans via the ``PlannerAgent``.  Clients can create
and manage per-session graphs, apply patches, retrieve the current
state, and request a plan for a given natural language command.

These endpoints form the backbone of the plan–act loop that
enables sophisticated multi-domain design interactions.  They are
stateless with respect to authentication; session identifiers must
be provided by the client and may map to user or project IDs in
a higher level service.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Body

from backend.schemas.odl import ODLGraph, GraphPatch, GraphDiff, OdlActRequest, OdlActResponse
from backend.schemas.ai import PlanResponse, AiCommandRequest
from backend.services.odl_graph_service import (
    init_session,
    get_graph,
    serialize_graph,
    apply_patch,
)
from backend.agents.planner_agent import PlannerAgent
from backend.agents.odl_domain_agents import (
    PVDesignAgent,
    WiringAgent,
    StructuralAgent,
    NetworkAgent,
    AssemblyAgent,
    BaseDomainAgent,
)

router = APIRouter()


@router.post("/odl/sessions", response_model=str)
async def create_odl_session(session_id: Annotated[str, Body(embed=True)]) -> str:
    """Initialise a new ODL graph session.

    The caller must provide a unique session ID (e.g. a UUID) to
    identify the graph.  If a graph already exists for the session it
    will be overwritten.

    Parameters
    ----------
    session_id: str
        The identifier for the session to initialise.

    Returns
    -------
    str
        The session ID, echoed back for convenience.
    """
    init_session(session_id)
    return session_id


@router.get("/odl/{session_id}", response_model=ODLGraph)
async def get_odl_graph(session_id: str) -> ODLGraph:
    """Retrieve the entire ODL graph for a session.

    Raises ``HTTPException(404)`` if the session does not exist.
    """
    try:
        g = get_graph(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_graph(g)


@router.patch("/odl/{session_id}", response_model=GraphDiff)
async def patch_odl_graph(session_id: str, patch: GraphPatch) -> GraphDiff:
    """Apply a patch to the ODL graph for a session.

    Returns a ``GraphDiff`` describing the changes that were applied.
    """
    try:
        diff = apply_patch(session_id, patch)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    return diff


@router.post("/odl/{session_id}/plan", response_model=PlanResponse)
async def plan_for_session(session_id: str, req: Annotated[AiCommandRequest, Body(embed=False)]) -> PlanResponse:
    """Generate a plan for a session based on a natural language command.

    This endpoint instantiates a ``PlannerAgent`` bound to the given
    session and delegates plan creation to it.  The plan is returned
    as a ``PlanResponse`` containing ordered tasks and quick actions.
    """
    try:
        # Ensure the session exists by fetching the graph
        get_graph(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    planner = PlannerAgent(session_id)
    tasks, actions = await planner.create_plan(req.command)
    return PlanResponse(tasks=tasks, quick_actions=actions if actions else None)


@router.post("/odl/{session_id}/act", response_model=OdlActResponse)
async def act_for_session(session_id: str, req: OdlActRequest) -> OdlActResponse:
    """Execute a plan task or quick action against the session's ODL graph.

    The planner generates task identifiers (e.g. 'generate_design') corresponding
    to domain-specific operations.  This endpoint dispatches to the appropriate
    domain agent, applies the resulting patch to the session graph, and returns
    both the patch and an optional design card.  The frontend should update its
    canvas representation based on the returned patch.
    """
    try:
        g = get_graph(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    task = (req.task_id or "").lower()
    action = (req.action or "").lower()

    # Route gather and design tasks to the PVDesignAgent.  Refinement goes to
    # the StructuralAgent, wiring to the WiringAgent.  Unknown tasks fall back
    # to the PVDesignAgent.
    if task in {
        "gather",
        "gather_requirements",
        "gather requirements",
        "prelim",
        "prelim_design",
        "generate_design",
        "generate_preliminary_design",
        "generate preliminary design",
        "generate design",
    } or (action and action.startswith("design")):
        agent: BaseDomainAgent = PVDesignAgent(session_id)
    elif task and task.startswith("wiring"):
        agent = WiringAgent(session_id)
    elif task and task.startswith("refine") or (action and action.startswith("validate")):
        agent = StructuralAgent(session_id)
    else:
        agent = PVDesignAgent(session_id)

    # Serialize the current graph for the agent and execute it
    graph_model = serialize_graph(g)
    patch, card = await agent.execute(task_id=task or action, graph=graph_model)
    # Apply the patch to the session graph
    apply_patch(session_id, patch)
    return OdlActResponse(patch=patch, card=card)
