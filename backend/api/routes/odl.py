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

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid
from typing import Any, Mapping

from backend.database.session import get_session
from backend.odl.schemas import ODLGraph, ODLPatch, PatchOp
from backend.odl.store import ODLStore
from backend.odl.views import layer_view
from backend.odl.serializer import view_to_odl
from backend.odl.layout import ensure_positions
from backend.utils.adpf import wrap_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/odl", tags=["ODL"])


def _fallback_text(view: dict) -> str:
    """Lossy but robust fallback text used when serializer fails."""
    lines = ["# ODL (fallback)"]
    for n in (view.get("nodes") or []):
        nid = n.get("id", "")
        ntype = n.get("type") or "generic"
        lines.append(f"node {nid} : {ntype}")
    for e in (view.get("edges") or []):
        src = e.get("source", "")
        tgt = e.get("target", "")
        lines.append(f"link {src} -> {tgt}")
    return "\n".join(lines) + "\n"


def _view_to_dict(view: Any) -> dict:
    """Return a plain dict from a LayerView or dict-like object."""
    if view is None:
        return {}
    if hasattr(view, "model_dump"):
        return view.model_dump()
    if isinstance(view, Mapping):
        return dict(view)
    return {}


def _synthesize_text_from_view(view: Any) -> str:
    """Render ODL text from a view, falling back to a minimal placeholder."""
    view_dict = _view_to_dict(view)
    try:
        return view_to_odl(view_dict)
    except Exception as ser_ex:
        logger.warning("ODL serializer failed; using fallback. err=%s", ser_ex)
        return _fallback_text(view_dict)


def _default_empty_view(session_id: str, layer: str) -> dict:
    return {
        "session_id": session_id,
        "base_version": 0,
        "layer": layer,
        "nodes": [],
        "edges": [],
    }


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


@router.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str, db: AsyncSession = Depends(get_session)):
    store = await _store_from_session(db)
    g = await store.get_graph(db, session_id)
    if not g:
        raise HTTPException(404, "Session not found")
    ops = [PatchOp(op_id=f"reset:{nid}", op="remove_node", value={"id": nid}) for nid in list(g.nodes.keys())]
    patch = ODLPatch(patch_id=f"reset:{uuid.uuid4()}", operations=ops)
    new_graph, new_version = await store.apply_patch_cas(db, session_id, expected_version=g.version, patch=patch)
    return {"session_id": session_id, "version": new_version}


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
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    """Return the current ODL view for a layer.

    Always injects positions and falls back to an empty view on any error so the
    canvas can render without hitting a 500.
    """
    layer_name = (layer or "single-line").strip().lower()
    try:
        store = await _store_from_session(db)
        g = await store.get_graph(db, session_id)
        if not g:
            logger.warning("ODL /view session not found sid=%s layer=%s", session_id, layer_name)
            response.headers["X-Graph-Version"] = "0"
            return _default_empty_view(session_id, layer_name)
        
        # Set version header for optimistic concurrency
        response.headers["X-Graph-Version"] = str(g.version)
        view = _view_to_dict(layer_view(g, layer_name))
        for n in (view.get("nodes") or []):
            n.setdefault("_render", {})
            n.setdefault("attrs", {})
            n["attrs"].setdefault("layer", layer_name)
        view = ensure_positions(view)
        for n in (view.get("nodes") or []):
            if "position" not in n and "pos" in n:
                n["position"] = n["pos"]
            if "pos" not in n and "position" in n:
                n["pos"] = n["position"]
        logger.info(
            "ODL /view sid=%s layer=%s nodes=%d edges=%d",
            session_id, layer_name, len(view.get("nodes") or []), len(view.get("edges") or []),
        )
        return view
    except Exception as ex:
        logger.exception("ODL /view failed sid=%s layer=%s: %s", session_id, layer_name, ex)
        response.headers["X-Graph-Version"] = "0"  # Set fallback version on error
        return _default_empty_view(session_id, layer_name)


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
        view = _view_to_dict(layer_view(g, layer_name))
        # version may appear as base_version or version depending on store impl
        version = int(view.get("base_version") or view.get("version") or g.version)
        nodes = len(view.get("nodes") or [])
        edges = len(view.get("edges") or [])
        logger.info(
            "Serialize ODL text sid=%s layer=%s v=%s nodes=%d edges=%d",
            session_id, layer_name, version, nodes, edges,
        )
        try:
            text = view_to_odl(view)
        except Exception as ser_ex:
            logger.warning("ODL serializer failed; using fallback. err=%s", ser_ex)
            text = _fallback_text(view)
        return {"session_id": session_id, "version": version, "text": text}
    except KeyError:
        logger.warning("ODL /text session not found sid=%s layer=%s", session_id, layer_name)
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as ex:
        logger.exception("ODL /text failed sid=%s layer=%s: %s", session_id, layer_name, ex)
        return {"session_id": session_id, "version": 0, "text": "# ODL (empty)\n"}


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


@router.get("/{session_id}/components", tags=["odl"])
async def get_odl_components(
    session_id: str,
    layer: str = Query("single-line"),
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    """
    Bridge endpoint: Convert ODL nodes to component format expected by frontend.
    This allows the canvas to render ODL data without major frontend changes.
    """
    try:
        store = await _store_from_session(db)
        g = await store.get_graph(db, session_id)

        # If session doesn't exist, return empty array (don't error)
        if not g:
            logger.info("ODL /components bridge: session %s not found, returning empty", session_id)
            response.headers["X-Graph-Version"] = "0"
            return []
        
        # Set version header for optimistic concurrency
        response.headers["X-Graph-Version"] = str(g.version)

        layer_name = (layer or "single-line").strip().lower()
        view = _view_to_dict(layer_view(g, layer_name))
        view = ensure_positions(view)

        # Convert ODL nodes to component format
        components = []
        for node in (view.get("nodes") or []):
            # Extract position from the layout helper
            pos = node.get("pos", {})
            x = pos.get("x", 0) if isinstance(pos, dict) else 0
            y = pos.get("y", 0) if isinstance(pos, dict) else 0

            component = {
                "id": node.get("id", ""),
                "name": node.get("type", "Unknown"),
                "type": node.get("type", "generic"),
                "x": x,
                "y": y,
                "layer": layer_name,
                "attrs": node.get("attrs", {}),
                "_render": node.get("_render", {}),
            }
            components.append(component)

        logger.info(
            "ODL /components bridge sid=%s layer=%s nodes=%d",
            session_id, layer_name, len(components),
        )
        return components
    except Exception as ex:
        # Never let exceptions escape - return empty array instead of 500
        logger.exception("ODL /components bridge failed sid=%s: %s", session_id, ex)
        response.headers["X-Graph-Version"] = "0"  # Set fallback version on error
        return []


@router.get("/{session_id}/links", tags=["odl"])
async def get_odl_links(
    session_id: str,
    layer: str = Query("single-line"),
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    """
    Bridge endpoint: Convert ODL edges to link format expected by frontend.
    This allows the canvas to render ODL connections without major frontend changes.
    """
    try:
        store = await _store_from_session(db)
        g = await store.get_graph(db, session_id)

        # If session doesn't exist, return empty array (don't error)
        if not g:
            logger.info("ODL /links bridge: session %s not found, returning empty", session_id)
            response.headers["X-Graph-Version"] = "0"
            return []
        
        # Set version header for optimistic concurrency
        response.headers["X-Graph-Version"] = str(g.version)

        layer_name = (layer or "single-line").strip().lower()
        view = _view_to_dict(layer_view(g, layer_name))

        # Convert ODL edges to link format
        links = []
        for i, edge in enumerate(view.get("edges") or []):
            link = {
                "id": f"{edge.get('source', '')}_{edge.get('target', '')}_{i}",
                "source_id": edge.get("source", ""),
                "target_id": edge.get("target", ""),
                "kind": edge.get("kind", "electrical"),
                "locked_in_layers": {},
                "path_by_layer": {},
            }
            links.append(link)

        logger.info(
            "ODL /links bridge sid=%s layer=%s edges=%d",
            session_id, layer_name, len(links),
        )
        return links
    except Exception as ex:
        # Never let exceptions escape - return empty array instead of 500
        logger.exception("ODL /links bridge failed sid=%s: %s", session_id, ex)
        response.headers["X-Graph-Version"] = "0"  # Set fallback version on error
        return []


@router.get("/{session_id}/debug", tags=["odl"])
async def debug_odl_session(
    session_id: str,
    layer: str = Query("single-line"),
    db: AsyncSession = Depends(get_session),
):
    """
    Debug endpoint: Get detailed information about an ODL session for troubleshooting.
    Returns the full graph, view, and layout information.
    """
    try:
        store = await _store_from_session(db)
        g = await store.get_graph(db, session_id)

        # Handle missing session gracefully
        if not g:
            return {
                "session_id": session_id,
                "error": "Session not found",
                "status": "empty",
                "graph": {"total_nodes": 0, "total_edges": 0, "node_types": [], "layers": []},
                "view": {"nodes_in_layer": 0, "edges_in_layer": 0, "nodes_with_positions": 0},
                "layout": {"nodes_positioned": 0, "sample_positions": []},
                "text_synthesis": {"fallback_text": "# ODL (empty session)"}
            }

        layer_name = (layer or "single-line").strip().lower()
        view = _view_to_dict(layer_view(g, layer_name))
        view_with_layout = ensure_positions(view)

        debug_info = {
            "session_id": session_id,
            "version": g.version,
            "layer": layer_name,
            "status": "found",
            "graph": {
                "total_nodes": len(g.nodes),
                "total_edges": len(g.edges),
                "node_types": list(set(n.type for n in g.nodes.values())),
                "layers": list(set(
                    n.attrs.get("layer", "default") if n.attrs else "default"
                    for n in g.nodes.values()
                )),
            },
            "view": {
                "nodes_in_layer": len(view.get("nodes") or []),
                "edges_in_layer": len(view.get("edges") or []),
                "nodes_with_positions": sum(
                    1 for n in (view.get("nodes") or [])
                    if n.get("pos") or ("x" in n and "y" in n)
                ),
            },
            "layout": {
                "nodes_positioned": len(view_with_layout.get("nodes") or []),
                "sample_positions": [
                    {
                        "id": n.get("id"),
                        "type": n.get("type"),
                        "pos": n.get("pos")
                    }
                    for n in (view_with_layout.get("nodes") or [])[:3]  # First 3 nodes
                ],
            },
            "text_synthesis": {
                "fallback_text": _synthesize_text_from_view(view),
            }
        }

        logger.info(
            "ODL debug sid=%s layer=%s graph_nodes=%d view_nodes=%d",
            session_id, layer_name, len(g.nodes), len(view.get("nodes") or []),
        )
        return debug_info
    except Exception as ex:
        logger.exception("ODL debug endpoint failed sid=%s: %s", session_id, ex)
        return {
            "session_id": session_id,
            "error": str(ex),
            "status": "error",
            "graph": {"total_nodes": 0, "total_edges": 0, "node_types": [], "layers": []},
            "view": {"nodes_in_layer": 0, "edges_in_layer": 0, "nodes_with_positions": 0},
            "layout": {"nodes_positioned": 0, "sample_positions": []},
            "text_synthesis": {"fallback_text": "# ODL (error occurred)"}
        }


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
    view = _view_to_dict(layer_view(g, layer))
    return {"changed": True, "version": g.version, "view": view}

# IMPORTANT: Register this router in your API aggregator or FastAPI app:
#   app.include_router(backend.api.routes.odl.router)
