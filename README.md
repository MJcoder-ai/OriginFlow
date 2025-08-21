# OriginFlow

> **Modular • AI-Powered • Standards-Compliant**

## Overview

> **Breaking Change (vNext)**  
> The server returns a **single response envelope** for AI actions: `thought`, `output.card`, `output.patch`, `status`, and optional `warnings`. Legacy top-level `card`/`patch` fields were removed. See `docs/BREAKING_CHANGES.md` and `backend/utils/adpf.py`.

OriginFlow is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users, offering drag-and-drop datasheets, AI auto-completion, and real-time compliance checks.

Recent updates introduce a **Multi-Domain Platform** with placeholder component support:

- **Placeholder Component System**: Start designing with generic components before real datasheets are available.
- **Enhanced Dynamic Planner**: Placeholder-aware task generation with multi-domain support (PV, battery, monitoring).
- **Component Selector Tool**: Intelligent replacement of placeholders with real parts based on requirements.
- **ODL Code View**: Live textual representation of designs with real-time updates.
- **Requirements Management**: Comprehensive form-based requirement collection and validation.
- **Version Control**: Complete graph versioning with patch history and revert capabilities.
- **Enhanced APIs**: 15+ new endpoints for ODL session management, component selection, and analysis.
- **Governance & Safety Policies**: Risk-based auto‑approval with per‑tenant thresholds, whitelists and a manual approval queue for high‑risk actions.
- **Extended Multi‑Domain Support**: Battery and monitoring tools automatically design energy storage and telemetry systems, deepening the placeholder‑first multi‑domain framework.
- **Observability & Learning**: Prometheus metrics (`/metrics`), optional OpenTelemetry tracing, and instrumented orchestrators provide visibility into latency and approval rates, laying the groundwork for continuous confidence calibration and adaptive learning.
- **Error Handling & Concurrency**: Custom exception types, idempotent graph updates with per‑session locks, and safe tool wrappers ensure robustness in the face of failures and concurrent access.
- **Sagas & Workflow Engine**: A lightweight saga engine orchestrates multi‑step design workflows, automatically rolling back applied patches on failure, and prepares the system for integration with Temporal.io or similar workflow orchestrators.
- **Enhanced Rule Engine**: Deterministic sizing extended to conduits and structural mounts; new functions compute recommended conduit cross‑sections and mount load capacities and validate installed components for NEC/IEC compliance.
- **Compliance & Rule Engine**: Enhanced rule engine with validation of installed wires and fuses; cross-layer validation tools check for unconnected components.
- **ADPF Integration**: All AI actions return results in a standard JSON envelope with meta-cognitive reasoning (`thought`), structured output and status. See `backend/utils/adpf.py` for details.
- **ODL as Single Source of Truth**: The design graph is stored as a versioned ODL state. All canvases/layers are projections over ODL (`/odl/.../view`). Patches are idempotent and applied with `If-Match` optimistic concurrency. See `docs/ODL_SPEC.md`.
- **Typed Tools (Phase 3)**: Domain logic lives in pure functions under `backend/tools/` that return `ODLPatch` objects. They are composed and applied by a single orchestrator. See `docs/TOOLS_CATALOG.md`.
- **Single Orchestrator (Phase 4)**: The `POST /ai/act` endpoint invokes a compact orchestrator that loads a minimal ODL slice, routes to a typed tool, enforces a risk decision, applies the patch with optimistic concurrency, and returns the unified ADPF envelope. See `docs/ORCHESTRATOR.md`.
- **Governance & Audit (Phase 6)**: Review-required actions go through `POST /approvals/propose` and `POST /approvals/{id}/decision`. Audit events record proposals, approvals and applied patches. See `docs/GOVERNANCE.md` and `docs/AUDIT_TRAIL.md`.
- **Domains (Phase 7)**: Multi-domain behavior is configured declaratively in `backend/domains/domain.yaml`. The orchestrator reads your session domain from ODL meta and uses domain mappings and risk overrides. See `docs/DOMAINS.md`.
- **Canvas Sync (Phase 8)**: Use lightweight `GET /odl/{id}/head` and `GET /odl/{id}/view_delta?since=...` for efficient redraws of specific layers. See `docs/FRONTEND_SYNC.md`.
- **Evals, QA & Performance (Phase 9)**: A tiny eval harness lives in `backend/evals/` with a CLI (`backend/scripts/run_evals.py`). It runs canonical scenarios (wiring, placeholder replacement) and enforces a minimal **budgeter** guard in the orchestrator to prevent oversized requests. See `docs/EVALS.md` and `backend/perf/budgeter.py`.

For additional governance details, see [docs/governance-approvals.md](docs/governance-approvals.md).

## Architecture Documentation

- [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
- [docs/ORCHESTRATOR.md](docs/ORCHESTRATOR.md)
- [docs/ODL_SPEC.md](docs/ODL_SPEC.md)
- [docs/TOOLS_CATALOG.md](docs/TOOLS_CATALOG.md)
- [docs/GOVERNANCE.md](docs/GOVERNANCE.md)
- [docs/AUDIT_TRAIL.md](docs/AUDIT_TRAIL.md)
- [docs/MEMORY.md](docs/MEMORY.md)
- [docs/DOMAINS.md](docs/DOMAINS.md)
- [docs/FRONTEND_SYNC.md](docs/FRONTEND_SYNC.md)
- [docs/EVALS.md](docs/EVALS.md)
- [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
- [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- [docs/BREAKING_CHANGES.md](docs/BREAKING_CHANGES.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## Contributing

- Fork the repository, create a branch, and submit pull requests.
- Run `flake8` and `pytest` before submitting.
- Add tests to maintain >90% coverage. Integration tests are marked with `@pytest.mark.integration` and can be skipped with `pytest -m 'not integration'`.
- See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## Recent Codebase Improvements

This codebase has been recently updated to improve consistency and maintainability:

### ✅ Code Style & Standards
- **Fixed deprecated typing imports**: Replaced `from typing import List, Dict, Optional` with modern annotations where possible
- **Standardized exception handling**: Replaced bare `except:` clauses with `except Exception:`
- **Updated coding standards**: All Python files now follow consistent style guidelines

### ✅ Dependencies & Configuration
- **Synchronized package versions**: Updated `requirements.txt` to match `pyproject.toml` versions
- **Added missing dependencies**: Included all required packages (fastapi-users, opentelemetry, etc.)
- **Fixed configuration consistency**: Ensured environment variables and settings are properly aligned

### ✅ Documentation Updates
- **Updated architecture overview**: Added notes about placeholder implementations and current status
- **Fixed documentation references**: Corrected outdated paths and links
- **Enhanced contributing guidelines**: Updated references to current documentation structure

### 📝 Implementation Status
Several services contain placeholder implementations that are ready for development:
- `backend/services/compatibility.py` - Rule validation stubs for domain-specific checks
- `backend/services/calculation_engines.py` - Engineering calculation engines (HVAC, water pumping)
- `backend/services/learning_agent_service.py` - ML model integration for action confidence scoring
- `backend/services/vector_store.py` - Vector database abstractions

### 🚀 Running the API locally
Use Uvicorn's log configuration to enable structured JSON logs without duplicates:

```bash
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --log-config backend/logging.dev.json
```

### 🧪 Testing
- Test infrastructure is in place but requires pytest installation: `pip install pytest pytest-asyncio`
- Backend tests located in `backend/tests/` and root `tests/` directory
- Set environment variables for a clean run:
  - `export DATABASE_URL="sqlite+aiosqlite:///:memory:"`
  - `export OPENAI_API_KEY="dummy"`
- Run tests with: `pytest -q`

## License

BSD License (pending legal review).

## Community & Support

- **Slack**: `#originflow-dev`
- **Email**: `maintainers@originflow.dev`
- **Docs**: https://docs.originflow.dev
- **Monitoring Guide**: [docs/DEPLOY_MONITORING.md](docs/DEPLOY_MONITORING.md)

Happy designing! 🚀
