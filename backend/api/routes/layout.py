from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.layout_provider import suggest_positions
from backend.services.edge_router import route_edges
from backend.services.odl_sync import rebuild_odl_for_session
from backend.services.wiring import AutoWiringService
from backend.api.deps import get_session

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


@router.post("/route")
async def route_orthogonal(
    session_id: str,
    layer: Literal["single_line", "high_level", "civil", "networking", "physical"] = Query("single_line"),
    session: AsyncSession = Depends(get_session),
):
    """Compute orthogonal routes for UNLOCKED links on a layer and persist them."""

    if get_current_snapshot is None:
        raise HTTPException(status_code=500, detail="Snapshot provider unavailable.")
    snapshot = await get_current_snapshot(session_id=session_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        routes = await route_edges(snapshot, layer=layer)
    except NotImplementedError as e:  # pragma: no cover - client-side routing
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:  # pragma: no cover - generic errors
        raise HTTPException(status_code=500, detail=f"Routing error: {e}")

    from backend.models.link import Link as LinkModel  # local import to avoid cycle

    for link in snapshot.links:
        eid = link.id or f"e_{link.source_id}_{link.target_id}"
        if eid not in routes:
            continue
        db_obj = await session.get(LinkModel, link.id)
        if db_obj is None:
            continue
        path = db_obj.path_by_layer or {}
        path[layer] = routes[eid]
        db_obj.path_by_layer = path
        locked = db_obj.locked_in_layers or {}
        locked[layer] = False
        db_obj.locked_in_layers = locked
        session.add(db_obj)

    await session.commit()
    try:  # best-effort ODL rebuild
        await rebuild_odl_for_session(session_id)
    except Exception:  # pragma: no cover - rebuild failures ignored
        pass

    return {"layer": layer, "routed": list(routes.keys())}


@router.post("/wire")
async def wire_missing(
    session_id: str,
    layer: Literal["single_line", "high_level", "civil", "networking", "physical"] = Query("single_line"),
):
    """Create missing links deterministically and route them orthogonally."""

    svc = AutoWiringService()
    result = await svc.wire_missing_and_route(session_id=session_id, layer=layer)
    return {"layer": layer, **result}
