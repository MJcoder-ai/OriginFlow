# backend/api/routes/files.py
"""File upload endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from openai import AsyncOpenAI
from backend.config import settings
from backend.api.deps import get_session, get_ai_client
from backend.schemas.file_asset import FileAssetRead, FileAssetUpdate
from backend.services.file_service import FileService, run_parsing_job
from backend.utils.id import generate_id

router = APIRouter()


# Create the uploads directory if it doesn't exist.
# <codex-marker>
# Resolve path relative to the backend package so changes to the working
# directory do not break file serving.
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/files/upload", response_model=FileAssetRead)
async def upload_file(
    session: AsyncSession = Depends(get_session),
    ai_client: AsyncOpenAI = Depends(get_ai_client),
    file: UploadFile = File(...),
) -> FileAssetRead:
    """Accept a file upload and persist its metadata."""
    service = FileService(session)
    asset_id = generate_id("asset")
    save_path = UPLOADS_DIR / asset_id
    save_path.mkdir(exist_ok=True)
    file_path = save_path / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    url = f"/static/uploads/{asset_id}/{file.filename}"
    size = file_path.stat().st_size
    obj = await service.create_asset(
        {
            "id": asset_id,
            "filename": file.filename,
            "mime": file.content_type,
            "size": size,
            "url": url,
        }
    )
    asset = FileAssetRead.model_validate(obj)

    if file.content_type == "application/pdf" and settings.openai_api_key != "test":
        try:
            parsed = await FileService.parse_datasheet(obj, session, ai_client)
            asset = FileAssetRead.model_validate(parsed)
        except Exception:
            # swallow parsing errors so upload still succeeds
            pass

    return asset


@router.get("/files/", response_model=list[FileAssetRead])
async def list_files(session: AsyncSession = Depends(get_session)) -> list[FileAssetRead]:
    """Return all uploaded file assets."""
    service = FileService(session)
    items = await service.list_assets()
    return [FileAssetRead.model_validate(it) for it in items]


@router.get("/files/{file_id}", response_model=FileAssetRead, summary="Get File Asset Status")
async def get_file_status(file_id: str, session: AsyncSession = Depends(get_session)) -> FileAssetRead:
    """Return a single file asset with parsing status."""
    asset = await FileService.get(session, file_id)
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")
    return FileAssetRead.model_validate(asset)


@router.post(
    "/files/{file_id}/parse",
    response_model=FileAssetRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI Datasheet Parsing",
)
async def trigger_datasheet_parsing(
    file_id: str,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    ai_client: AsyncOpenAI = Depends(get_ai_client),
) -> FileAssetRead:
    """Kick off AI parsing as a background task."""
    asset = await FileService.get(session, file_id)
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")
    if asset.mime != "application/pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF datasheet.")

    updated_asset = await FileService.trigger_parsing(asset, session)
    background_tasks.add_task(run_parsing_job, asset.id, session, ai_client)
    return FileAssetRead.model_validate(updated_asset)


@router.patch("/files/{file_id}", response_model=FileAssetRead, summary="Update Parsed Datasheet Data")
async def update_parsed_data(
    file_id: str,
    update_data: FileAssetUpdate,
    session: AsyncSession = Depends(get_session),
) -> FileAssetRead:
    asset = await FileService.get(session, file_id)
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")

    updated = await FileService.update_asset(asset, update_data, session)
    return FileAssetRead.model_validate(updated)


@router.get(
    "/files/{file_id}/file",
    response_class=FileResponse,
    summary="Download original file for preview",
)
async def download_file(
    file_id: str, session: AsyncSession = Depends(get_session)
) -> FileResponse:
    """Stream the original uploaded file from disk."""
    asset = await FileService.get(session, file_id)
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(asset.local_path),
        media_type=asset.mime,
        filename=asset.filename,
    )

