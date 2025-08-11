"""Routes for diff and undo/redo functionality."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.odl_graph_service import (
    get_patch_diff,
    revert_to_version,
    get_graph,
)

router = APIRouter(prefix="/versions", tags=["versions"])


class RevertRequest(BaseModel):
    target_version: int

@router.get("/{session_id}/diff")
async def get_diff(session_id: str, from_version: int, to_version: int):
    """
    Return the list of patches needed to move from `from_version` to `to_version`.
    """
    patches = get_patch_diff(session_id, from_version, to_version)
    if patches is None:
        raise HTTPException(status_code=404, detail="No patches found for version range")
    return {"patches": patches}


@router.post("/{session_id}/revert")
async def revert(session_id: str, req: RevertRequest):
    """
    Revert a session graph to the specified version.
    """
    success = await revert_to_version(session_id, req.target_version)
    if not success:
        raise HTTPException(status_code=400, detail="Unable to revert to requested version")
    graph = await get_graph(session_id)
    return {"detail": f"Session reverted to version {req.target_version}", "version": graph.graph.get("version")}
