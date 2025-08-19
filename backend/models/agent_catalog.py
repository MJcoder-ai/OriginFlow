from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import String, JSON, DateTime, Integer, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models import Base


class AgentCatalog(Base):
    """
    Canonical catalog entry for an agent (name/domain/description).
    One-to-many with AgentVersion; per-tenant enablement lives in TenantAgentState.
    """
    __tablename__ = "agent_catalog"

    # Agent name is stable (snake_case), acts as business key.
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    domain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    risk_class: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # e.g. low|medium|high
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)     # e.g. {"actions": ["add_component", ...]}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    versions = relationship("AgentVersion", back_populates="catalog", cascade="all,delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AgentCatalog name={self.name} domain={self.domain}>"


class AgentVersion(Base):
    """
    Versioned agent spec blobs (draft/staged/published/archived).
    """
    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint("agent_name", "version", name="uq_agent_versions_name_version"),
        Index("ix_agent_versions_agent_status", "agent_name", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), ForeignKey("agent_catalog.name"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft|staged|published|archived
    spec: Mapped[dict] = mapped_column(JSON)                           # Validated AgentSpec (see schemas)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    validation_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # UUID as string for portability
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    catalog = relationship("AgentCatalog", back_populates="versions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AgentVersion {self.agent_name}@{self.version} status={self.status}>"


class TenantAgentState(Base):
    """
    Tenant-scoped enablement/config overrides for each agent.
    A tenant can pin a specific published version, or follow latest published.
    """
    __tablename__ = "tenant_agent_state"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_name", name="uq_tenant_agent_state_tenant_agent"),
        Index("ix_tenant_agent_state_tenant_agent", "tenant_id", "agent_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(100))
    agent_name: Mapped[str] = mapped_column(String(100), ForeignKey("agent_catalog.name"))
    enabled: Mapped[bool] = mapped_column(default=True)
    pinned_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    config_override: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    updated_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TenantAgentState tenant={self.tenant_id} agent={self.agent_name} enabled={self.enabled}>"

