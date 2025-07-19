# backend/api/routes/files.py
"""File upload endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.schemas.file_asset import FileAssetRead, FileAssetUpdate
from backend.services.file_service import FileService
from backend.utils.id import generate_id

router = APIRouter()


# Create the uploads directory if it doesn't exist
UPLOADS_DIR = Path("backend/static/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/files/upload", response_model=FileAssetRead)
async def upload_file(
    session: AsyncSession = Depends(get_session), file: UploadFile = File(...)
) -> FileAssetRead:
    """Accept a file upload and persist its metadata."""
    service = FileService(session)
    asset_id = generate_id("asset")
    save_path = UPLOADS_DIR / asset_id
    save_path.mkdir()
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
    return FileAssetRead.model_validate(obj)


@router.get("/files/", response_model=list[FileAssetRead])
async def list_files(session: AsyncSession = Depends(get_session)) -> list[FileAssetRead]:
    """Return all uploaded file assets."""
    service = FileService(session)
    items = await service.list_assets()
    return [FileAssetRead.model_validate(it) for it in items]


@router.post("/files/{file_id}/parse", response_model=FileAssetRead, summary="Trigger AI Datasheet Parsing")
async def trigger_datasheet_parsing(
    file_id: str, session: AsyncSession = Depends(get_session)
) -> FileAssetRead:
    asset = await FileService.get(session, file_id)
    if not asset:
        raise HTTPException(status_code=404, detail="File not found")
    if asset.mime != "application/pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF datasheet.")

    parsed = await FileService.parse_datasheet(asset, session)
    return FileAssetRead.model_validate(parsed)


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

