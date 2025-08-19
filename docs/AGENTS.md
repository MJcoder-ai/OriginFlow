# Agents Catalog (runtime & persistence)

This document describes how agents are discovered at runtime (in-memory registry) and
how they are now **persisted per tenant** with **versioning, RBAC and LLM-assisted authoring**.

## Runtime (unchanged)
The runtime still uses `backend/agents/registry.py` to register agents available to the orchestrator.

## New persistence layer
- **Tables**
  - `agent_catalog`: stable agent identity and metadata.
  - `agent_versions`: versioned specs with status `draft|staged|published|archived`.
  - `tenant_agent_state`: per-tenant enable/disable, pinned version, config overrides.
- **Migrations**
  - `alembic/versions/20250819_01_agents_persistence.py` creates all three tables.
- **Service**
  - `backend/services/agent_catalog_service.py` provides helpers to create drafts, publish versions,
    and resolve effective version for a tenant.
- **Schema**
  - `backend/schemas/agent_spec.py` validates agent specs (Pydantic v2).

## RBAC
Endpoints use `backend/auth/dependencies.require_permission` with the following permissions:
- `agents.read` – list catalog/state
- `agents.edit` – create drafts, update tenant state, call authoring assistant
- `agents.publish` – publish versions

## API
- `GET /api/v1/odl/agents` – runtime registry (existing)
- `GET /api/v1/odl/agents/state?tenant_id=...` – list tenant-scoped state + effective version
- `POST /api/v1/odl/agents/drafts` – create a new **draft**: `{ spec: AgentSpecModel }`
- `POST /api/v1/odl/agents/{agent_name}/publish` – publish draft/staged (optional `{version}` to target)
- `POST /api/v1/odl/agents/{agent_name}/state` – update tenant enablement/pin/config
- `POST /api/v1/odl/agents/assist/synthesize-spec` – LLM to generate a new spec from an idea
- `POST /api/v1/odl/agents/assist/refine-spec` – LLM to refine an existing spec

## Frontend
- Sidebar now includes **Agents**.
- `AgentsPanel` lists tenant state and supports:
  - toggle enable/disable
  - pin a published version
  - publish latest
  - draft authoring via **Synthesize** / **Refine** workflow (JSON is editable before saving as Draft).

## Notes / Future work
- The orchestrator can optionally hydrate runtime agents from the latest **published** specs resolved by tenant;
  this patch intentionally keeps runtime unchanged for safety.
- Validation is conservative (regex, shape, required fields). You can extend `AgentSpecModel` with stricter
  action schemas and tool registries when you finalize domain-specific tools.

