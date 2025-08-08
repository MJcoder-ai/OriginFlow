from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.schemas.attributes import AttributeViewItem, AttributePatch, ErrorResponse
from backend.services.attribute_catalog_service import AttributeCatalogService

router = APIRouter(prefix="/api/v1/components", tags=["components"])

def get_catalog_service():
    # Wire to your real repo / DI container; placeholder returns stateless service
    return AttributeCatalogService(repo=None)

@router.get("/{component_id}/attributes/view", response_model=list[AttributeViewItem], responses={500: {"model": ErrorResponse}})
async def get_component_attributes_view(component_id: str, request: Request, svc: AttributeCatalogService = Depends(get_catalog_service)):
    # TODO: Implement real view assembly from DB. Returning empty list to unblock frontend wiring.
    return []

@router.patch("/{component_id}/attributes", status_code=204, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def patch_component_attributes(component_id: str, patches: List[AttributePatch], request: Request, svc: AttributeCatalogService = Depends(get_catalog_service)):
    # TODO: Apply patches (upsert/delete/verify) via repo + versioning + audit
    return JSONResponse(status_code=204, content=None)

@router.post("/{component_id}/confirm-close", status_code=204, responses={409: {"model": ErrorResponse}})
async def confirm_and_close(component_id: str, request: Request):
    # TODO: set is_human_verified=true and mark current attribute versions verified. Do NOT trigger parse here.
    return JSONResponse(status_code=204, content=None)

@router.post("/{component_id}/reanalyze", status_code=202)
async def reanalyze_component(component_id: str, request: Request):
    # TODO: clear extracted images/metadata (not manual), enqueue parse job, return job id
    return {"job_id": "job_placeholder"}

def include_component_attributes_routes(app):
    app.include_router(router)
