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
    Response,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from openai import AsyncOpenAI
from backend.config import settings
from backend.api.deps import get_session, get_ai_client
from backend.auth.dependencies import require_file_upload
from backend.auth.models import User
from backend.schemas.file_asset import FileAssetRead, FileAssetUpdate
from backend.services.file_service import FileService, run_parsing_job
from backend.utils.id import generate_id
from backend.security.file_validation import validate_uploaded_file, generate_safe_filename, is_safe_path

# Typing helper for JSON-like return values
from typing import Any

router = APIRouter()


# Create the uploads directory if it doesn't exist.
# <codex-marker>
# Resolve path relative to the backend package so changes to the working
# directory do not break file serving.
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/files/upload", response_model=FileAssetRead)
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    ai_client: AsyncOpenAI = Depends(get_ai_client),
    current_user: User = Depends(require_file_upload),
) -> FileAssetRead:
    """Accept a file upload with comprehensive security validation."""
    
    # 1. Validate the uploaded file
    validation_result = await validate_uploaded_file(file)
    
    # 2. Generate safe filename and paths
    safe_filename = generate_safe_filename(
        validation_result['filename'], 
        str(current_user.id)
    )
    
    service = FileService(session)
    asset_id = generate_id("asset")
    save_path = UPLOADS_DIR / asset_id
    save_path.mkdir(exist_ok=True, mode=0o755)
    
    # 3. Validate path safety
    file_path = save_path / safe_filename
    if not is_safe_path(str(file_path.relative_to(UPLOADS_DIR)), str(UPLOADS_DIR)):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file path"
        )
    
    # 4. Secure file writing
    try:
        # Write file content securely
        with file_path.open("wb") as buffer:
            # Read and write in chunks to handle large files
            chunk_size = 8192
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
        
        # Set restrictive file permissions
        file_path.chmod(0o644)
        
    except Exception as e:
        # Clean up on failure
        if file_path.exists():
            file_path.unlink()
        if save_path.exists() and not any(save_path.iterdir()):
            save_path.rmdir()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    url = f"/static/uploads/{asset_id}/{safe_filename}"
    size = file_path.stat().st_size
    # 5. Store file metadata
    payload = {
        "id": asset_id,
        "filename": safe_filename,  # Store safe filename
        "mime": validation_result["detected_mime"],  # Use validated MIME type
        "size": size,
        "url": url,
    }
    # Compute hash for potential future auditing but do not persist it until
    # the database schema includes a ``file_hash`` column.
    file_hash = validation_result["hash"]  # noqa: F841 - reserved for future use
    # Only track uploader when authentication is enabled and schema supports it
    if settings.enable_auth:
        _ = current_user.id  # Placeholder for future ``uploaded_by`` persistence
    obj = await service.create_asset(payload)
    asset = FileAssetRead.model_validate(obj)

    if (
        file.content_type == "application/pdf"
        and settings.openai_api_key != "test"
    ):
        try:
            parsed = await FileService.parse_datasheet(
                obj, session, ai_client
            )
            asset = FileAssetRead.model_validate(parsed)
        except Exception:
            # swallow parsing errors so upload still succeeds
            pass

    return asset


@router.get("/files/", response_model=list[FileAssetRead])
async def list_files(
    session: AsyncSession = Depends(get_session),
) -> list[FileAssetRead]:
    """Return all uploaded file assets."""
    service = FileService(session)
    items = await service.list_assets()
    return [FileAssetRead.model_validate(it) for it in items]


@router.get(
    "/files/{file_id}",
    response_model=FileAssetRead,
    summary="Get File Asset Status",
)
async def get_file_status(
    file_id: str,
    session: AsyncSession = Depends(get_session),
) -> FileAssetRead:
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
        raise HTTPException(
            status_code=400, detail="File is not a PDF datasheet."
        )

    updated_asset = await FileService.trigger_parsing(asset, session)
    background_tasks.add_task(run_parsing_job, asset.id, session, ai_client)
    return FileAssetRead.model_validate(updated_asset)


@router.patch(
    "/files/{file_id}",
    response_model=FileAssetRead,
    summary="Update Parsed Datasheet Data",
)
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


# ---------------------------------------------------------------------------
# Image management endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/files/{file_id}/images",
    summary="List images associated with a datasheet",
)
async def list_images(
    file_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    service = FileService(session)
    try:
        images = await service.list_images(file_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return images


@router.post(
    "/files/{file_id}/images",
    summary="Upload additional images for a datasheet",
)
async def upload_images(
    file_id: str,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
) -> list[FileAssetRead]:
    service = FileService(session)
    try:
        saved = await service.upload_images(file_id, files)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [FileAssetRead.model_validate(img) for img in saved]


@router.delete(
    "/files/{file_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an image associated with a datasheet",
    response_class=Response,
)
async def delete_image_endpoint(
    file_id: str,
    image_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = FileService(session)
    try:
        await service.delete_image(file_id, image_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/files/{file_id}/images/{image_id}/primary",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Set an image as the primary thumbnail for a datasheet",
    response_class=Response,
)
async def set_primary_image_endpoint(
    file_id: str,
    image_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    service = FileService(session)
    try:
        await service.set_primary_image(file_id, image_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
