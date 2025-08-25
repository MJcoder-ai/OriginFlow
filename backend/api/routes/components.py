"""Component endpoints: CRUD for schematic components and ingestion."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.components import (
    ComponentIngestRequest,
    ComponentIngestResponse,
)
from backend.schemas.component import Component as ComponentSchema, ComponentCreate, ComponentUpdate
from backend.services.component_db_service import ComponentDBService
from backend.services.component_service import ComponentService
from backend.database.session import get_session

router = APIRouter(prefix="/components", tags=["components"])

component_db_service = ComponentDBService()


@router.post("/ingest", response_model=ComponentIngestResponse)
async def ingest_component(req: ComponentIngestRequest) -> ComponentIngestResponse:
    """Ingest a parsed component datasheet into the library."""
    try:
        component_id = await component_db_service.ingest(
            category=req.category,
            part_number=req.part_number,
            attributes=req.attributes,
        )
    except Exception as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ComponentIngestResponse(component_id=component_id)


# --- CRUD endpoints used by the canvas ---

@router.get("/", response_model=list[ComponentSchema])
async def list_components(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
) -> list[ComponentSchema]:
    service = ComponentService(session)
    items = await service.list(skip=skip, limit=limit)
    return [ComponentSchema.model_validate(it) for it in items]


@router.post("/", response_model=ComponentSchema, status_code=status.HTTP_201_CREATED)
async def create_component(
    payload: ComponentCreate,
    session: AsyncSession = Depends(get_session),
    x_user_command: str | None = Header(default=None),  # Optional: if FE passes original prompt
) -> ComponentSchema:
    service = ComponentService(session)
    obj = await service.create(payload)
    
    # If the frontend is still hitting this endpoint directly from an AI action,
    # we can optionally enforce the intent firewall here, too (defensive).
    # NOTE: we DO NOT mutate payload here (already persisted). Prefer /ai/apply for AI flows.
    # This header is only for telemetry/future safeguards.
    if x_user_command:
        try:
            from backend.ai.ontology import resolve_canonical_class
            req_cls = resolve_canonical_class(x_user_command)
            if req_cls and req_cls != obj.type:
                # Log a mismatch so we can catch any remaining bypasses of /ai/apply
                import logging
                logger = logging.getLogger("backend.ai.firewall")
                logger.warning("Intent mismatch: requested=%s, created=%s id=%s", req_cls, obj.type, obj.id)
        except (ImportError, AttributeError, KeyError) as e:
            # Ontology resolution failed - log for debugging but don't fail the component creation
            import logging
            logger = logging.getLogger("backend.ai.firewall")
            logger.debug("Failed to resolve canonical class for command %s: %s", x_user_command, e)
    
    return ComponentSchema.model_validate(obj)


@router.get("/{component_id}", response_model=ComponentSchema)
async def get_component(
    component_id: str,
    session: AsyncSession = Depends(get_session),
) -> ComponentSchema:
    service = ComponentService(session)
    obj = None
    
    # Try to get from component database first, but handle missing table gracefully
    try:
        obj = await service.get(component_id)
    except Exception:
        # If component database doesn't exist or has issues, skip to ODL fallback
        pass
    
    if not obj:
        # If not found in component DB, try to find in ODL graph
        # This handles ODL-generated components like inv_FRONIUS_
        try:
            from backend.database.session import get_session as get_db_session
            from backend.odl.store import ODLStore
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"Searching for ODL component: {component_id}")
            
            async for db in get_db_session():
                odl_store = ODLStore()
                
                # Search across all sessions for this component
                try:
                    from sqlalchemy import text
                    session_result = await db.execute(text("SELECT DISTINCT session_id FROM odl_graphs LIMIT 10"))
                    session_ids = [row[0] for row in session_result.fetchall()]
                    logger.info(f"Found {len(session_ids)} ODL sessions to search")
                    
                    for session_id in session_ids:
                        logger.info(f"Checking session: {session_id}")
                        try:
                            graph = await odl_store.get_graph(db, session_id)
                            if graph:
                                logger.info(f"Session {session_id} has {len(graph.nodes)} nodes")
                                if component_id in graph.nodes:
                                    node = graph.nodes[component_id]
                                    logger.info(f"Found component {component_id} in session {session_id}")
                                    
                                    # Convert ODL node to Component schema
                                    component_data = {
                                        "id": component_id,
                                        "name": node.attrs.get("name", f"{node.type} {component_id}"),
                                        "type": node.type,
                                        "standard_code": node.attrs.get("part_number", f"ODL-{component_id}"),
                                        "x": node.attrs.get("x", 100),
                                        "y": node.attrs.get("y", 100),
                                        "layer": node.attrs.get("layer", "single-line")
                                    }
                                    return ComponentSchema.model_validate(component_data)
                        except Exception as e:
                            logger.warning(f"Error checking session {session_id}: {e}")
                            continue
                except Exception as e:
                    logger.error(f"Error searching ODL sessions: {e}")
                break
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"ODL fallback failed for {component_id}: {e}")
    
    if not obj:
        raise HTTPException(404, "Component not found")
    
    return ComponentSchema.model_validate(obj)


@router.patch("/{component_id}", response_model=ComponentSchema)
async def update_component(
    component_id: str,
    payload: ComponentUpdate,
    session: AsyncSession = Depends(get_session),
) -> ComponentSchema:
    service = ComponentService(session)
    obj = await service.update(component_id, payload.model_dump(exclude_none=True))
    return ComponentSchema.model_validate(obj)


@router.delete(
    "/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_component(
    component_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = ComponentService(session)
    await service.delete(component_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
