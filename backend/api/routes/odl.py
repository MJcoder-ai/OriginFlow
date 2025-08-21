"""
FastAPI routes for ODL single source of truth.

Endpoints:
- POST /odl/sessions                 -> create a new ODL graph (version=1)
- GET  /odl/{session_id}             -> retrieve full ODL graph
- POST /odl/{session_id}/patch       -> apply ODLPatch (CAS via If-Match)
- GET  /odl/{session_id}/view        -> derived projection for a layer

Headers:
- If-Match: <version> (required for PATCH)
- Idempotency-Key: <uuid> (optional; preferred at patch level via patch_id/op_id)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from backend.database.session import get_session
from backend.odl.schemas import ODLGraph, ODLPatch
from backend.odl.store import ODLStore
from backend.odl.views import layer_view
from backend.odl.serializer import view_to_odl
from backend.utils.adpf import wrap_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/odl", tags=["ODL"])


async def _store_from_session(db: AsyncSession) -> ODLStore:
    store = ODLStore()
    await store.init_schema(db)
    return store


@router.post("/sessions", response_model=ODLGraph)
async def create_session(session_id: str, db: AsyncSession = Depends(get_session)) -> ODLGraph:
    store = await _store_from_session(db)
    existing = await store.get_graph(db, session_id)
    if existing:
        return existing
    return await store.create_graph(db, session_id)


@router.get("/{session_id}", response_model=ODLGraph)
async def get_graph(session_id: str, db: AsyncSession = Depends(get_session)) -> ODLGraph:
    store = await _store_from_session(db)
    g = await store.get_graph(db, session_id)
    if not g:
        raise HTTPException(404, "Session not found")
    return g


@router.post("/{session_id}/patch")
async def apply_patch(
    session_id: str,
    patch: ODLPatch,
    if_match: int = Header(..., alias="If-Match"),
    db: AsyncSession = Depends(get_session),
):
    store = await _store_from_session(db)
    try:
        g, new_version = await store.apply_patch_cas(db, session_id, expected_version=if_match, patch=patch)
    except KeyError:
        raise HTTPException(404, "Session not found")
    except ValueError as ve:
        raise HTTPException(409, str(ve))  # Version mismatch -> 409 Conflict
    except Exception as e:
        raise HTTPException(400, str(e))

    return wrap_response(
        thought=f"Applied patch {patch.patch_id} to session {session_id}",
        card={"title": "Patch Applied", "subtitle": f"New version: {new_version}"},
        patch={"session_id": session_id, "version": new_version},
        status="complete",
    )


@router.get("/{session_id}/view")
async def get_view(
    session_id: str,
    layer: str = Query("single-line"),
    db: AsyncSession = Depends(get_session),
):
    store = await _store_from_session(db)
    g = await store.get_graph(db, session_id)
    if not g:
        raise HTTPException(404, "Session not found")
    view = layer_view(g, layer)
    return view


@router.get("/sessions/{session_id}/text")
async def get_odl_text(
    session_id: str,
    layer: str = Query("single-line"),
    db: AsyncSession = Depends(get_session),
):
    """
    Returns canonical ODL text for the given session/layer.
    Response: { "session_id": "...", "version": <int>, "text": "<odl>" }
    """
    layer_name = (layer or "single-line").strip().lower()
    try:
        store = await _store_from_session(db)
        g = await store.get_graph(db, session_id)
        if not g:
            logger.warning("ODL /text session not found sid=%s layer=%s", session_id, layer_name)
            raise HTTPException(status_code=404, detail="Session not found")
        view = layer_view(g, layer_name)
        # version may appear as base_version or version depending on store impl
        version = int(view.get("base_version") or view.get("version") or g.version)
        nodes = len(view.get("nodes") or [])
        edges = len(view.get("edges") or [])
        logger.info("Serialize ODL text sid=%s layer=%s v=%s nodes=%d edges=%d",
                    session_id, layer_name, version, nodes, edges)
        text = view_to_odl(view)
        return {"session_id": session_id, "version": version, "text": text}
    except KeyError:
        logger.warning("ODL /text session not found sid=%s layer=%s", session_id, layer_name)
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as ex:
        # Never let exceptions escape – Uvicorn would emit a 500 without CORS headers.
        logger.exception("ODL /text failed sid=%s layer=%s: %s", session_id, layer_name, ex)
        return JSONResponse(status_code=500, content={
            "error_code": "ODL_TEXT_FAILED",
            "message": "Failed to render ODL text",
        })


@router.get("/{session_id}/head")
async def get_head(session_id: str, db: AsyncSession = Depends(get_session)):
    """
    Lightweight head endpoint for canvas sync. Returns current version only.
    """
    store = await _store_from_session(db)
    g = await store.get_graph(db, session_id)
    if not g:
        raise HTTPException(404, "Session not found")
    return {"session_id": session_id, "version": g.version}


@router.get("/{session_id}/view_delta")
async def get_view_delta(
    session_id: str,
    since: int = Query(..., description="Client's last known version"),
    layer: str = Query("single-line"),
    db: AsyncSession = Depends(get_session),
):
    """
    Return `{changed, version, view?}` for efficient canvas refresh.
    If no change since `since`, returns `changed=false` with current head version.
    """
    store = await _store_from_session(db)
    g = await store.get_graph(db, session_id)
    if not g:
        raise HTTPException(404, "Session not found")
    if g.version <= since:
        return {"changed": False, "version": g.version}
    view = layer_view(g, layer)
    return {"changed": True, "version": g.version, "view": view}

# IMPORTANT: Register this router in your API aggregator or FastAPI app:
#   app.include_router(backend.api.routes.odl.router)
