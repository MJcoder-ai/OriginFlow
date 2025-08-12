"""Component endpoints: CRUD for schematic components and ingestion."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.components import (
    ComponentIngestRequest,
    ComponentIngestResponse,
)
from backend.schemas.component import Component as ComponentSchema, ComponentCreate, ComponentUpdate
from backend.services.component_db_service import ComponentDBService
from backend.services.component_service import ComponentService
from backend.api.deps import get_session

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
) -> ComponentSchema:
    service = ComponentService(session)
    obj = await service.create(payload)
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


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(
    component_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ComponentService(session)
    await service.delete(component_id)
    return None
