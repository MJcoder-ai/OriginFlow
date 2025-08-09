"""ORM models for hierarchical component records and their documents.

These models define a product family (base component) and its discrete
variants.  They allow flexible, domain-agnostic attributes and track
trust levels, lifecycle status, regional availability and compliance.
Associated documents (datasheets, warranties, installation guides) are
linked to the base component and may optionally apply to specific variants.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import datetime
from sqlalchemy import String, Boolean, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from backend.models import Base


class HierarchicalComponent(Base):
    """Hierarchical component record supporting bases and variants.

    This table is named ``components`` to align with the database migration.  It
    stores both base components (where ``variant_id`` is NULL) and their
    discrete variants.  A base component represents a product family, while
    variants capture specific SKUs or revisions.  Shared and variant-specific
    attributes are stored in a JSONB ``attributes`` column, and additional
    metadata (trust level, lifecycle status, available regions, etc.) is
    captured in dedicated columns.
    """

    __tablename__ = "components"

    base_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    variant_id: Mapped[Optional[str]] = mapped_column(String, primary_key=True, nullable=True)
    is_base_component: Mapped[bool] = mapped_column(Boolean, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    mpn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    status: Mapped[str] = mapped_column(String, default="Active")
    trust_level: Mapped[str] = mapped_column(String, default="User-Added")
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False)
    configurable_options: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    compliance_tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    photos_icons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    available_regions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"HierarchicalComponent(base_id={self.base_id!r}, variant_id={self.variant_id!r}, "
            f"brand={self.brand!r}, mpn={self.mpn!r}, version={self.version!r}, "
            f"status={self.status!r}, trust={self.trust_level!r})"
        )


class ComponentDocument(Base):
    """Document associated with a hierarchical component base.

    Documents (datasheets, warranties, installation guides, help guides, etc.)
    are linked to the ``base_id`` of a component family.  A document marked
    ``is_shared`` applies to all variants, while ``covered_variants`` can be
    used to restrict the document to a subset of variants.  The table is
    named ``documents`` to align with the Alembic migration.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    base_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    asset_id: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, default="1.0.0")
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    covered_variants: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"ComponentDocument(id={self.id!r}, type={self.type!r}, base_id={self.base_id!r})"

