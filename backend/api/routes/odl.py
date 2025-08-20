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

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.odl.schemas import ODLGraph, ODLPatch
from backend.odl.store import ODLStore
from backend.odl.views import layer_view
from backend.utils.adpf import wrap_response

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

# IMPORTANT: Register this router in your API aggregator or FastAPI app:
#   app.include_router(backend.api.routes.odl.router)
