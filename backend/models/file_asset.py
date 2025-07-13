# backend/models/file_asset.py
"""ORM model representing uploaded files."""
from __future__ import annotations

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.models import Base


class FileAsset(Base):
    """Metadata for uploaded files stored in S3."""

    __tablename__ = "file_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    component_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("components.id", ondelete="SET NULL"), nullable=True
    )

