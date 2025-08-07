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
    # When this asset is derived from or uploaded for another file (e.g.
    # an image extracted from a PDF datasheet), ``parent_asset_id`` stores
    # the ID of that parent asset.  Top-level uploaded files will have this
    # field set to ``None``.
    parent_asset_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # ``FileAsset`` records may be associated with a schematic component when a
    # datasheet or image is uploaded from the canvas.  The core component table
    # was renamed to ``schematic_components`` but this model was not updated,
    # resulting in a broken foreign key mapping at runtime.  Align the
    # ``component_id`` foreign key with the current table name so SQLAlchemy can
    # resolve the relationship correctly.
    component_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("schematic_components.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    parsed_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parsing_status: Mapped[str | None] = mapped_column(String, nullable=True)
    parsing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_human_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    # Fields related to images extracted from PDF datasheets.  When a
    # ``FileAsset`` represents an image produced by the datasheet parser,
    # ``is_extracted`` will be true.  ``is_primary`` indicates the preferred
    # thumbnail for the associated component.  ``width`` and ``height`` store
    # pixel dimensions when available.  These fields are optional so that
    # existing files without images are unaffected.
    is_extracted: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def local_path(self) -> Path:
        """Return the local filesystem path for this asset."""
        from backend.api.routes.files import UPLOADS_DIR

        return UPLOADS_DIR / self.id / self.filename

