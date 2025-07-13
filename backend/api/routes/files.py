# backend/api/routes/files.py
"""File upload endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session
from backend.schemas.file import FileAsset
from backend.services.file_service import FileService
from backend.utils.id import generate_id

router = APIRouter()


# Create the uploads directory if it doesn't exist
UPLOADS_DIR = Path("backend/static/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/files/upload", response_model=FileAsset)
async def upload_file(
    session: AsyncSession = Depends(get_session), file: UploadFile = File(...)
) -> FileAsset:
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
    return FileAsset.model_validate(obj)

