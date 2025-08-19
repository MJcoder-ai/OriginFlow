from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.registry import registry
from backend.api.deps import get_current_user
from backend.api.deps import get_session
from backend.schemas.agent_spec import (
    AgentDraftCreate,
    AgentPublishRequest,
    TenantAgentStateUpdate,
    AgentAssistSynthesizeRequest,
    AgentAssistRefineRequest,
    AgentSpecModel,
)
from backend.services.agent_catalog_service import AgentCatalogService
from backend.services.agent_author_service import AgentAuthorService
from backend.services.agent_hydrator import AgentHydrator
from backend.auth.dependencies import require_permission

router = APIRouter(prefix="/api/v1/odl/agents", tags=["Agents"])

@router.get("/")
async def list_agents():
    """
    Returns the currently registered agents in memory (runtime registry).
    This is unchanged and remains the quick way to introspect active agents.
    """
    return [
        {
            "name": a.name,
            "domain": a.domain,
            "patterns": [p.value for p in a.patterns],
            "llm_tools": list(a.llm_tools),
            "capabilities": a.capabilities,
            "config": a.config,
        }
        for a in registry.get_agents()
    ]


@router.get("/state")
async def list_tenant_agent_state(
    tenant_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
    _=Depends(require_permission("agents.read")),
):
    """
    Return tenant-scoped enablement and effective published spec (if any).
    If tenant_id omitted, derive from user (if your auth model carries it).
    """
    # Derive tenant if not explicitly provided
    t_id = tenant_id or getattr(user, "tenant_id", None) or "default"
    out: list[dict] = []
    # Use catalog to list known agents
    from sqlalchemy import select
    from backend.models.agent_catalog import AgentCatalog
    rows = (await session.execute(select(AgentCatalog))).scalars().all()
    for cat in rows:
        effective, state = await AgentCatalogService.resolved_agent_for_tenant(session, t_id, cat.name)
        out.append(
            {
                "agent_name": cat.name,
                "display_name": cat.display_name,
                "enabled": bool(state.enabled) if state else True,
                "pinned_version": state.pinned_version if state else None,
                "effective_version": effective.version if effective else None,
                "status": effective.status if effective else None,
                "domain": cat.domain,
                "capabilities": cat.capabilities,
            }
        )
    return out


@router.post("/drafts", status_code=201)
async def create_draft_version(
    payload: AgentDraftCreate,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
    _=Depends(require_permission("agents.edit")),
):
    """
    Validate and persist a new DRAFT version of an agent spec.
    """
    spec: AgentSpecModel = payload.spec
    draft = await AgentCatalogService.create_or_update_draft(session, spec, getattr(user, "id", None))
    await session.commit()
    return {"agent_name": draft.agent_name, "version": draft.version, "status": draft.status}


@router.post("/{agent_name}/publish", status_code=200)
async def publish_agent_version(
    agent_name: str,
    payload: AgentPublishRequest,
    session: AsyncSession = Depends(get_session),
    _=Depends(require_permission("agents.publish")),
):
    """
    Publish a draft/staged version. If version omitted, latest is published.
    """
    try:
        row = await AgentCatalogService.publish_latest(session, agent_name, payload.version)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    await session.commit()
    AgentHydrator.invalidate()
    return {"agent_name": row.agent_name, "version": row.version, "status": row.status}


@router.post("/{agent_name}/state", status_code=200)
async def update_tenant_state(
    agent_name: str,
    payload: TenantAgentStateUpdate,
    tenant_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
    _=Depends(require_permission("agents.edit")),
):
    """
    Enable/disable an agent for a tenant, optionally pin a published version,
    and/or set config overrides.
    """
    t_id = tenant_id or getattr(user, "tenant_id", None) or "default"
    row = await AgentCatalogService.update_state(
        session,
        t_id,
        agent_name,
        enabled=payload.enabled,
        pinned_version=payload.pinned_version,
        config_override=payload.config_override,
        updated_by_id=getattr(user, "id", None),
    )
    await session.commit()
    AgentHydrator.invalidate(t_id)
    return {
        "tenant_id": row.tenant_id,
        "agent_name": row.agent_name,
        "enabled": row.enabled,
        "pinned_version": row.pinned_version,
        "updated_at": row.updated_at.isoformat(),
    }


@router.post("/assist/synthesize-spec", status_code=200)
async def assist_synthesize(req: AgentAssistSynthesizeRequest, _=Depends(require_permission("agents.edit"))):
    """
    LLM-assisted authoring: draft a brand new spec from an idea.
    """
    spec = await AgentAuthorService.synthesize(req)
    return {"spec": spec.model_dump()}


@router.post("/assist/refine-spec", status_code=200)
async def assist_refine(req: AgentAssistRefineRequest, _=Depends(require_permission("agents.edit"))):
    """
    LLM-assisted authoring: refine an existing spec using critique.
    """
    spec = await AgentAuthorService.refine(req)
    return {"spec": spec.model_dump()}

