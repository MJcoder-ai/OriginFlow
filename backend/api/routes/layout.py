from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Literal

from backend.services.layout_provider import suggest_positions

try:
    from backend.services.snapshot_provider import get_current_snapshot  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    get_current_snapshot = None

router = APIRouter(prefix="/layout", tags=["layout"])


@router.get("/suggest")
async def layout_suggest(
    session_id: str,
    layer: Literal["single_line", "high_level", "civil", "networking", "physical"] = Query("single_line"),
):
    """
    Suggest positions for UNLOCKED nodes on a layer.
    Frontend can apply these suggestions by PATCHing each component's layout/lock.
    """
    if get_current_snapshot is None:
        raise HTTPException(status_code=500, detail="Snapshot provider unavailable.")
    snapshot = await get_current_snapshot(session_id=session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        positions = await suggest_positions(snapshot, layer=layer)
        return {"layer": layer, "positions": positions}
    except NotImplementedError as e:  # pragma: no cover - provider-specific
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:  # pragma: no cover - generic errors
        raise HTTPException(status_code=500, detail=f"Layout error: {e}")
