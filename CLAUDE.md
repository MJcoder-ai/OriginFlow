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

### ODL (OriginFlow Design Language)
ODL is the core data model - a versioned graph format that serves as the single source of truth. All canvases and UI layers are projections of ODL state.

Key ODL endpoints:
- `POST /api/v1/odl/sessions?session_id=...` - Create/get session
- `GET /api/v1/odl/{id}/view?layer=...` - Get layer projection
- `POST /api/v1/ai/act` - Execute AI actions with optimistic concurrency

### Orchestrator Pattern
The system uses a single orchestrator (`/ai/act`) that:
1. Minimizes context for AI calls
2. Routes tasks to typed tools
3. Enforces risk/governance policies
4. Applies patches with optimistic concurrency (If-Match headers)

### Typed Tools Architecture
Pure functions in `backend/tools/` that:
- Take ODL state + parameters as input
- Return `ODLPatch` objects
- Have no database dependencies
- Are easily testable

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
- `backend/odl/` - ODL schemas, patches, store, views
- `backend/services/` - Database-connected services
- `backend/api/routes/` - REST API endpoints
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