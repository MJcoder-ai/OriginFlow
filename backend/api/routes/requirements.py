"""Routes for updating user requirements during the gather phase."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.services.odl_graph_service import get_graph, save_graph

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("/{session_id}")
async def update_requirements(session_id: str, requirements: dict) -> dict:
    """
    Update the requirements (target_power, roof_area, budget, etc.) for the
    given session.  Stores the values on the graph’s metadata.
    """
    graph = await get_graph(session_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Session not found")
    graph.graph.setdefault("requirements", {}).update(requirements)
    await save_graph(session_id, graph)
    return {"detail": "Requirements updated"}
