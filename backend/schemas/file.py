# backend/schemas/file.py
"""Schemas for file upload operations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FileAsset(BaseModel):
    id: str
    filename: str
    mime: str
    size: int
    url: str
    component_id: str | None = None

    model_config = ConfigDict(from_attributes=True)

