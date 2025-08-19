from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple
import hashlib
import json
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.agent_catalog import AgentCatalog, AgentVersion, TenantAgentState
from backend.schemas.agent_spec import AgentSpecModel

logger = logging.getLogger(__name__)


def _checksum_spec(spec: dict) -> str:
    # Stable hash for dedup/version checks
    m = hashlib.sha256()
    m.update(json.dumps(spec, sort_keys=True).encode("utf-8"))
    return m.hexdigest()


class AgentCatalogService:
    """
    Manages agent catalog/version records and tenant-scoped state.
    This does not change the running in-memory registry; it is a source of truth
    for governance + UI. Runtime can choose to hydrate from these entries.
    """

    # ---------- Catalog ----------
    @staticmethod
    async def ensure_catalog(session: AsyncSession, spec: AgentSpecModel) -> AgentCatalog:
        row = await session.scalar(select(AgentCatalog).where(AgentCatalog.name == spec.name))
        if row:
            # Update metadata (non-destructive)
            row.display_name = spec.display_name
            row.description = spec.description
            row.domain = spec.domain
            row.risk_class = spec.risk_class
            row.capabilities = {"actions": [c.action for c in spec.capabilities]}
            return row
        row = AgentCatalog(
            name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            domain=spec.domain,
            risk_class=spec.risk_class,
            capabilities={"actions": [c.action for c in spec.capabilities]},
        )
        session.add(row)
        return row

    # ---------- Versions ----------
    @staticmethod
    async def next_version(session: AsyncSession, agent_name: str) -> int:
        current = await session.scalar(
            select(func.max(AgentVersion.version)).where(AgentVersion.agent_name == agent_name)
        )
        return (current or 0) + 1

    @staticmethod
    async def create_or_update_draft(
        session: AsyncSession,
        spec: AgentSpecModel,
        created_by_id: Optional[str],
    ) -> AgentVersion:
        await AgentCatalogService.ensure_catalog(session, spec)
        # Always create a fresh draft on spec change for traceability
        version = await AgentCatalogService.next_version(session, spec.name)
        checksum = _checksum_spec(spec.model_dump())
        av = AgentVersion(
            agent_name=spec.name,
            version=version,
            status="draft",
            spec=spec.model_dump(),
            checksum=checksum,
            created_by_id=created_by_id,
        )
        session.add(av)
        return av

    @staticmethod
    async def set_status(
        session: AsyncSession, agent_name: str, version: int, status: str
    ) -> AgentVersion:
        row = await session.scalar(
            select(AgentVersion).where(
                AgentVersion.agent_name == agent_name, AgentVersion.version == version
            )
        )
        if not row:
            raise ValueError("Version not found")
        row.status = status
        if status == "published":
            row.published_at = datetime.utcnow()
        return row

    @staticmethod
    async def publish_latest(
        session: AsyncSession, agent_name: str, requested_version: Optional[int] = None
    ) -> AgentVersion:
        if requested_version is not None:
            return await AgentCatalogService.set_status(session, agent_name, requested_version, "published")
        # choose newest draft/staged
        row = await session.scalar(
            select(AgentVersion)
            .where(
                AgentVersion.agent_name == agent_name,
                AgentVersion.status.in_(("draft", "staged")),
            )
            .order_by(AgentVersion.version.desc())
        )
        if not row:
            raise ValueError("No draft/staged version to publish")
        row.status = "published"
        row.published_at = datetime.utcnow()
        return row

    @staticmethod
    async def latest_published(
        session: AsyncSession, agent_name: str
    ) -> Optional[AgentVersion]:
        return await session.scalar(
            select(AgentVersion)
            .where(AgentVersion.agent_name == agent_name, AgentVersion.status == "published")
            .order_by(AgentVersion.version.desc())
        )

    # ---------- Tenant state ----------
    @staticmethod
    async def get_or_create_state(
        session: AsyncSession, tenant_id: str, agent_name: str
    ) -> TenantAgentState:
        row = await session.scalar(
            select(TenantAgentState).where(
                TenantAgentState.tenant_id == tenant_id,
                TenantAgentState.agent_name == agent_name,
            )
        )
        if row:
            return row
        row = TenantAgentState(tenant_id=tenant_id, agent_name=agent_name, enabled=True)
        session.add(row)
        return row

    @staticmethod
    async def update_state(
        session: AsyncSession,
        tenant_id: str,
        agent_name: str,
        *,
        enabled: Optional[bool] = None,
        pinned_version: Optional[int] = None,
        config_override: Optional[dict] = None,
        updated_by_id: Optional[str] = None,
    ) -> TenantAgentState:
        row = await AgentCatalogService.get_or_create_state(session, tenant_id, agent_name)
        if enabled is not None:
            row.enabled = enabled
        if pinned_version is not None:
            row.pinned_version = pinned_version
        if config_override is not None:
            row.config_override = config_override
        row.updated_by_id = updated_by_id
        row.updated_at = datetime.utcnow()
        return row

    @staticmethod
    async def resolved_agent_for_tenant(
        session: AsyncSession, tenant_id: str, agent_name: str
    ) -> Tuple[Optional[AgentVersion], Optional[TenantAgentState]]:
        """
        Returns (effective_version, tenant_state). Resolution rules:
        - If tenant pinned_version set -> that published version.
        - Else latest published.
        """
        st = await AgentCatalogService.get_or_create_state(session, tenant_id, agent_name)
        effective: Optional[AgentVersion] = None
        if st.pinned_version:
            effective = await session.scalar(
                select(AgentVersion).where(
                    AgentVersion.agent_name == agent_name,
                    AgentVersion.version == st.pinned_version,
                    AgentVersion.status == "published",
                )
            )
        if not effective:
            effective = await AgentCatalogService.latest_published(session, agent_name)
        return effective, st

