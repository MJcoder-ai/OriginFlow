"""Component ingestion endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.components import (
    ComponentIngestRequest,
    ComponentIngestResponse,
)
from backend.services.component_db_service import ComponentDBService

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
