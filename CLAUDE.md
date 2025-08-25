# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OriginFlow is a browser-based, AI-powered design environment for creating standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users with drag-and-drop datasheets, AI auto-completion, and real-time compliance checks.

The system uses a multi-domain platform architecture with:
- **Python FastAPI backend** - Main API server with orchestrated AI tools
- **TypeScript React frontend** - Canvas-based design interface built with Vite
- **ODL (OriginFlow Design Language)** - Custom format for representing designs as versioned graphs
- **Docker Compose** - Complete development environment setup

## Development Commands

### Backend (Python)

The backend uses Poetry for dependency management. Always use Poetry for package operations:

```bash
# Install dependencies
poetry install

# Start development server
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --log-config backend/logging.dev.json

# Run tests
poetry run pytest -q

# Run tests excluding integration tests  
poetry run pytest -m 'not integration'

# Lint and type checking
poetry run flake8
poetry run pyright

# Create database migrations
poetry run alembic revision --autogenerate -m "Description"
poetry run alembic upgrade head
```

### Frontend (TypeScript/React)

The frontend is a Vite-based React application:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint and type checking
npm run lint
npm run type-check
```

### Docker Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after changes
docker-compose up --build -d
```

### Testing and CI

```bash
# Run end-to-end smoke test
chmod +x scripts/smoke.sh
./scripts/smoke.sh

# Run with custom port
PORT=8001 ./scripts/smoke.sh
```

## Architecture and Key Concepts

### ODL (OriginFlow Design Language) - Formal Schema
ODL is the core data model - a versioned graph format with formal Pydantic schemas that serves as the single source of truth. The formal ODL schema provides enterprise-grade validation, type safety, and consistent attribute access patterns.

**Formal ODL Components:**
- **ODLGraph** - Unified graph model with session management and versioning
- **ODLNode** - Component nodes with formal `node.data` attribute access
- **ODLEdge** - Connections with `source_id/target_id` naming and port awareness
- **Standard Types** - 45+ component types, 21+ edge kinds, and 5 node layers

**Key ODL endpoints:**
- `POST /api/v1/odl/sessions?session_id=...` - Create/get session
- `GET /api/v1/odl/{id}/view?layer=...` - Get layer projection  
- `POST /api/v1/ai/act` - Execute AI actions with optimistic concurrency

**Attribute Access Patterns:**
- Component attributes: `node.data["power"]` (formal schema)
- Connection metadata: `edge.attrs["layer"]` (formal schema)
- Port-level connections: `edge.source_port`, `edge.target_port`

### Orchestrator Pattern
The system uses a single orchestrator (`/ai/act`) that:
1. Minimizes context for AI calls
2. Routes tasks to typed tools
3. Enforces risk/governance policies
4. Applies patches with optimistic concurrency (If-Match headers)

### Typed Tools Architecture  
Pure functions in `backend/tools/` that:
- Take formal ODL state + parameters as input
- Return `ODLPatch` objects with formal schema compliance
- Have no database dependencies  
- Are easily testable with formal validation

**Important:** All tools now use the formal ODL schema. Legacy dict-based nodes/edges are not supported. Use:
- `ODLGraph` instances for graph data
- `node.data` for component attributes
- `edge.source_id/target_id` for connections (formal naming)
- `edge.attrs` for connection metadata (formal schema)
- `edge.kind` for connection categorization (electrical, mechanical, etc.)

### Enterprise AI Wiring System
The platform includes a comprehensive AI-driven wiring generation system with enhanced validation and topology generation:

**AI Wiring Tool (`ai_generate_wiring`):**
- **Enhanced Panel Grouping** - Advanced algorithms with minimum string size validation
- **Enterprise Electrical Topology** - Centralized, validated edge creation with compliance checking
- LLM-powered wiring suggestions with advanced reasoning
- Vector store integration for similar design retrieval  
- Formal ODL schema integration with proper patch operations

**Available via:**
- **Orchestrator**: `POST /ai/act` with `task: "ai_generate_wiring"`
- **Direct API**: `POST /ai/wiring` with AI-specific parameters
- **Tool Integration**: Formal `backend.tools.ai_wiring.generate_ai_wiring`

**Enhanced Features (Latest):**
- **Enhanced Panel Grouping** (`backend.ai.panel_grouping`):
  - Multi-strategy grouping (spatial, electrical, shading-aware, performance-optimized)
  - Configurable minimum string size validation with `enforce_min_string_size`
  - Flexible final string handling with `allow_undersized_final_string`
  - NEC compliance checking and electrical validation

- **Enterprise Electrical Topology** (`backend.tools.enterprise_electrical_topology`):
  - Centralized connection validation with `EnterpriseElectricalTopology` class
  - Enhanced `ConnectionSuggestion` dataclass with confidence scoring and reasoning
  - Comprehensive port compatibility validation and compliance checking
  - Formal ODL schema integration using `source_id/target_id` and `attrs`
  - Support for 8 standard connection types (DC string, AC branch, grounding, etc.)

**Key Features:**
- Port-aware edge creation with formal schema validation
- Optimistic concurrency control with graph versioning
- Enterprise pipeline with metrics, audit trails, and error handling
- NEC/IEC compliance validation with detailed compliance notes
- Multi-domain support with declarative configuration

### Multi-Domain Support
- Domains configured declaratively in `backend/domains/domain.yaml`
- Supports PV solar, battery, monitoring systems
- Placeholder-first workflow: design with generic components, replace with real parts later

## Database Configuration

For development, use file-backed SQLite:
```bash
mkdir -p .localdb
export DATABASE_URL="sqlite+aiosqlite:///$PWD/.localdb/originflow.db"
```

For testing, in-memory SQLite is configured with StaticPool for proper `uvicorn --reload` behavior.

## Key File Locations

### Backend Structure
- `backend/main.py` - FastAPI application entry point
- `backend/orchestrator/` - Core orchestration logic
- `backend/tools/` - Pure function tools for design operations
  - `backend/tools/ai_wiring.py` - Enterprise AI wiring tool with formal schema
  - `backend/tools/enterprise_electrical_topology.py` - Enhanced electrical topology generation
- `backend/ai/` - AI-powered design automation
  - `backend/ai/wiring_ai_pipeline.py` - Enterprise AI wiring pipeline
  - `backend/ai/panel_grouping.py` - Enhanced panel grouping with minimum string validation
- `backend/schemas/odl.py` - Formal ODL schema definitions (ODLGraph, ODLNode, ODLEdge)
- `backend/odl/` - ODL patches, store, views
- `backend/services/` - Database-connected services
- `backend/api/routes/` - REST API endpoints
  - `backend/api/routes/ai_act.py` - AI orchestration and wiring endpoints
- `backend/governance/` - Approval workflows and audit trails
- `backend/domains/` - Multi-domain configuration

### Frontend Structure
- `frontend/src/components/` - React UI components
- `frontend/src/services/api.ts` - Backend API client
- `frontend/src/layout/` - Canvas layout and rendering logic

### Configuration
- `pyproject.toml` - Python dependencies and project config
- `frontend/package.json` - Node.js dependencies and scripts
- `docker-compose.yml` - Full development environment
- `backend/logging.dev.json` - Structured logging configuration

## Important Implementation Notes

### Error Handling
- All AI actions return ADPF envelope format: `{thought, output: {card?, patch?}, status, warnings?}`
- Custom exception types in `backend/utils/exceptions.py`
- Comprehensive error middleware with structured logging

### Governance & Compliance
- Risk-based auto-approval with manual queue for high-risk actions
- Audit trail for all design changes
- Per-tenant policy configuration
- NEC/IEC compliance validation

### Performance & Monitoring
- Prometheus metrics at `/metrics` endpoint  
- OpenTelemetry tracing support
- Request budgeting in `backend/perf/budgeter.py`
- Structured JSON logging

### Placeholder Implementations
Several services contain TODO stubs ready for development:
- `backend/services/compatibility.py` - Domain-specific rule validation
- `backend/services/calculation_engines.py` - Engineering calculations (HVAC, pumping)
- `backend/services/learning_agent_service.py` - ML confidence scoring
- `backend/services/vector_store.py` - Vector database abstractions

## Testing Strategy

- Unit tests with >90% coverage requirement
- Integration tests marked with `@pytest.mark.integration`
- End-to-end smoke test in `scripts/smoke.sh`
- Eval scenarios in `backend/evals/` for regression testing

## Troubleshooting

### Blank Canvas Issues
1. **Command UI semantics**
   - Typing in the Command bar requests a fresh **LongPlan** for that text.
   - “Run” on a task calls `POST /ai/act` with the task’s tool id + args.
   - “Run All” executes tasks in the returned order, respecting dependencies client-side.
2. Reset session: `POST /api/v1/odl/sessions/{session_id}/reset`
3. Verify session creation and ODL view endpoints

### Database Issues
- Ensure parent directories exist before creating file-backed SQLite databases
- Use `backend/logging.dev.json` for structured logging during development
- Check that all required environment variables are set