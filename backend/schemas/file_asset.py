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
    uploaded_at: datetime | None = None
    parsed_payload: dict | None = None
    parsed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class FileAssetUpdate(BaseModel):
    parsed_payload: dict
