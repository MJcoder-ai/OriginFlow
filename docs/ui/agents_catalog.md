# Agents Catalog (MVP)

This page documents the initial **Agents** catalog UI and the minimal backend
endpoints it relies on. It introduces:

- A new **Agents** entry in the sidebar
- The **Agents** main panel with search, domain filter, card grid, and a detail drawer
- Route-scoped toolbar actions: **New Agent** / **Refresh** only when the Agents panel is active
- A “New Agent” modal that accepts a JSON spec or loads a starter template

## Backend Endpoints

- `GET /api/v1/agents` – Returns a lightweight list of agents (name,
  display_name, version, domain, risk_class, capabilities).
- `GET /api/v1/agents/{name}` – Returns the full spec for a single agent (and
  an `enabled` flag placeholder).
- `POST /api/v1/agents/register` – Registers a new agent from a JSON spec (MVP
  validation).
- `POST /api/v1/agents/{name}/enable|disable` – Stub toggles for now (extend to
  persisted state later).
- `GET /api/v1/agents/templates` – A few simple starter templates for the “New
  Agent” modal.

These endpoints are implemented in `backend/api/routes/agents.py`. They build
on the existing agent registry and **do not override advanced orchestration**.

## Frontend

- **Sidebar**: adds “Agents” under Projects/Components/Settings.
- **MainPanel**: routes `route === 'agents'` to `AgentsPanel`.
- **Toolbar**: route-scoped buttons; shows “New Agent” and “Refresh” for the
  Agents panel.
- **AgentsPanel**: lists all agents, provides search + domain filter, and a
  detail drawer with enable/disable.
- **NewAgentModal**: lets admins start from a template or paste a JSON spec;
  calls `/agents/register`.

## Next Milestones

- Persist agent enable/disable states and versions in DB (per-tenant).
- LLM-assisted spec generation w/ validation and sandbox tests.
- Fine-grained capabilities & RBAC for who can create/enable agents.

