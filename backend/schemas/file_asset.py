"""Schemas for file asset operations."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FileAssetBase(BaseModel):
    filename: str
    mime: str
    size: int
    url: str


class FileAssetRead(FileAssetBase):
    id: str
    parent_asset_id: str | None = None
    uploaded_at: datetime | None = None
    parsed_payload: dict | None = None
    parsed_at: datetime | None = None
    parsing_status: str | None = None
    parsing_error: str | None = None
    is_human_verified: bool | None = None

    # Fields for image assets.  These will be populated for images
    # extracted from PDF datasheets or uploaded manually via the images API.
    is_extracted: bool | None = None
    is_primary: bool | None = None
    width: int | None = None
    height: int | None = None

    model_config = ConfigDict(from_attributes=True)


class FileAssetUpdate(BaseModel):
    parsed_payload: dict
    is_human_verified: bool | None = None
