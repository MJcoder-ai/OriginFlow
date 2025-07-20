# backend/models/file_asset.py
"""ORM model representing uploaded files."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    JSON,
    func,
    Boolean,
    Text,
)
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
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    parsed_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parsing_status: Mapped[str | None] = mapped_column(String, nullable=True)
    parsing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_human_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    @property
    def local_path(self) -> Path:
        """Return the local filesystem path for this asset."""
        from backend.api.routes.files import UPLOADS_DIR

        return UPLOADS_DIR / self.id / self.filename

