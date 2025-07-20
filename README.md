# OriginFlow

> **Modular • AI-Powered • Standards-Compliant** – A scalable platform for engineering design, starting with a browser-based environment for creating schematics and bills-of-materials.

---

## 1. Overview
`OriginFlow` is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into fully-connected, standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users, offering features like drag-and-drop datasheets, AI auto-completion, and real-time compliance checks. The platform is built to be modular, scalable, and extensible, with a focus on reliability and user experience.

---

## 2. Key Features
- **Engineering Canvas**: A drag-and-drop interface for creating and editing schematics with AI-driven auto-completion, industry-standard naming, WebGL rendering, CRDT-based offline sync, and port-based connections between components. Links are created by dragging from an output port to an input port, with ports highlighting during the drag. Component dragging is separate from linking, so accidental moves are avoided. Connection lines now align precisely with each port for clearer diagrams.
- **Customer Project Wizard**: A guided interface for non-technical users to plan projects with AI suggestions and cost estimation.
- **AI-Driven Datasheet Processing**: Asynchronous parsing pipeline with status tracking, Chain-of-Thought extraction and a Reviewer AI for higher accuracy.
- **Media Management**: Upload or capture component images/videos, validated by AI with Octopart API integration.
- **Standards Compliance Engine**: Real-time validation against industry standards (e.g., IEC 81346) with webhook-driven revalidation.
- **Workflow Orchestration**: Self-hosted Temporal.io for reliable execution of complex workflows, including Saga Pattern for rollbacks.
- **Extensibility**: Plug-in framework for components, AI models, and workflows via Component Pack Studio and marketplace.
- **Observability**: Grafana dashboards, OpenTelemetry traces, and Workflow Visibility Dashboard for monitoring.
- **Properties Panel with AI Chat**: Manage components via the Component Library in the sidebar, edit selected component properties, and collaborate with an AI assistant.
- **Voice Mode Chat Input**: Click the microphone icon to dictate messages. The icon glows red while listening and automatically stops a couple seconds after you finish speaking.
- **Component Deletion by Name**: Remove components via the AI assistant or UI by referencing the component's name.
- **AI Governance**: MLMD for model versioning and drift detection.
- **Performance Benchmarks**:
  | **Nodes** | **CPU (cores)** | **RAM (GB)** |
  |-----------|-----------------|--------------|
  | 100       | 2               | 4            |
  | 1000      | 4               | 8            |
  | 2000      | 8               | 16           |

---

## 3. Supported Technologies
- **Frontend**: React 18.2, TypeScript 5.3, react-flow 11.10, Tailwind CSS 3.4, Zustand 4.5, @dnd-kit/core 6.0, clsx 2.1, shadcn/ui 0.8, React Joyride 2.7, react-tooltip 5.2, lucide-react 0.371
- **Backend**: FastAPI 0.109, Python 3.11, PostgreSQL 16, Redis 7.2
- **AI Services**: pgvector 0.4.1, LlamaIndex, spaCy, sentence-transformers/all-MiniLM-L6-v2, YOLOv8, OpenCV, MLMD 0.2
- **Workflow Orchestration**: Temporal.io 1.22 (self-hosted)
- **Authentication**: Supabase
- **File Storage**: S3-compatible (e.g., Cloudflare R2, MinIO)
- **Offline Storage**: IndexedDB via Dexie.js
- **Observability**: Grafana 10.2, OpenTelemetry 1.18, Loki 2.9

---

## 4. Getting Started

### 4.1 Prerequisites
- Node.js ≥18, npm ≥9
- Python ≥3.11, Poetry ≥1.8
- PostgreSQL 16, Redis 7.2, Kafka, HashiCorp Vault (or Docker Compose)
- Temporal.io self-hosted setup

### 4.2 Installation
```bash
git clone https://github.com/your-org/OriginFlow.git
cd OriginFlow
poetry install --with dev
npm install
cp .env.example .env && nano .env
docker compose up -d
poetry run alembic upgrade head
```

### 4.3 Emergency Shutdown
```bash
# Activate emergency shutdown
curl -X POST -H "Authorization: Bearer $EMERGENCY_TOKEN" \
  https://api.originflow.com/emergency_shutdown
```

### 4.4 UI Development
```bash
cd frontend
npm install
npm run dev
```

The UI uses `lucide-react` for icons. Run `npm install` after pulling updates to ensure the package is installed.

The dev server expects `index.html` in the frontend project root. Ensure
`@vitejs/plugin-react` is listed in `devDependencies`.

---

## 5. Configuration
Configuration is managed via environment variables and YAML files:
```yaml
# shared/config/backend.yaml
database:
  url: postgresql://user:password@localhost:5432/originflow
temporal:
  host: localhost:7233
ai_services:
  model_path: /path/to/models
```

See `.env.example` for required environment variables:
- `API_KEY`: API key for external services (e.g., Octopart).
- `DATABASE_URL`: Database connection string. If omitted, the backend uses a
  local SQLite file (`sqlite:///./originflow.db`) with a configuration that
  allows concurrent API requests.
- `VITE_API_URL`: Frontend base URL for the backend API.
- `TEMPORAL_HOST`: Host for self-hosted Temporal.io.

### ⚡ Quick-start (AI subsystem)
```bash
# 1. clone + install
git clone https://github.com/<org>/originflow.git
cd originflow
poetry install
cp .env.example .env           # fill in OPENAI_API_KEY & DATABASE_URL
# The backend shares a single OpenAI client loaded from this file.

# 2. run DB migrations
alembic upgrade head
# Migration scripts automatically detect SQLite vs PostgreSQL and
# use the appropriate timestamp function for backfilling.

# 3. start backend + frontend
poetry run uvicorn backend.main:app --reload --host 0.0.0.0
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Test the AI endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/ai/command \
     -H "Content-Type: application/json" \
     -d '{"command":"add a panel"}'
```

### 🔍 Design analysis

```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze-design \
     -H "Content-Type: application/json" \
     -d @snapshot.json
```
Where `snapshot.json` looks like:

```json
{
  "command": "validate my design",
  "snapshot": {
    "components": [],
    "links": []
  }
}
```

The API responds with an array of `AiAction` objects that the UI can apply.

### New AI commands

* **remove _{name}_** – deletes by name.
* **analyse / validate** – full snapshot audit.
* **what is the bill of materials** – shows modal with unique part list.
* **organise / optimise layout** – neatly re-positions nodes.

---

## 6. Usage Examples

### 6.1 Run OriginFlow
```bash
# Run backend
poetry run originflow-backend

# Run frontend
npm run start
```

### 6.2 Add a New Component
```python
from backend.models.data_models import Component
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewComponent(Component):
    def __init__(self, standard_code: str):
        super().__init__(standard_code=standard_code)
        # Additional initialization
        self.description = "Custom component"
```

### 6.3 Add a New API Endpoint
```python
from fastapi import APIRouter
from shared.compliance.regulatory_checks import compliance_tag

router = APIRouter()

@compliance_tag(regulation="IEC 81346")
@router.get("/new_endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

### 6.4 Add a New AI Model
```python
from ai_services.models.ai_models import AIServices
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewAIModel(AIServices):
    def __init__(self):
        super().__init__()
        # Model-specific initialization
        self.model_path = "/path/to/new_model"
```

### 6.5 Add a New Workflow
```python
from backend.services.workflow_engine import WorkflowEngine
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewWorkflow(WorkflowEngine):
    def __init__(self):
        super().__init__()
        # Workflow-specific initialization
        self.nodes = [{"id": "node1", "type": "custom_action"}]
```

### 6.6 Observability
```bash
docker compose -f docker-compose.yml -f docker-compose.observability.yml up
```
Access Grafana at `http://localhost:3000`.

### 6.7 Troubleshooting Drag-and-Drop
If dragging new components onto the canvas stops working after customizations,
ensure that drag-and-drop handlers execute **synchronously**. Libraries such as
`dnd-kit` expect handlers like `handleDragEnd` to finish immediately so they can
perform cleanup. Call asynchronous store actions (e.g. `addComponent`) without
`await` inside these handlers.
If newly dropped components disappear, verify that `addComponent` adds the
frontend-only `ports` array before storing the component.
If uploaded datasheets appear but cannot be dragged from the Component Library, ensure each entry uses `useDraggable` with a unique id.
If linking two components causes the card itself to move, ensure the drag handle
is separate from the port elements. The UI expects only the transparent card
overlay to be draggable while the ports handle linking exclusively.

When persisting component positions, the backend expects integer coordinates.
The store now rounds drag deltas before sending a PATCH request so fractional
values do not trigger validation errors.

If the application serves an outdated build, run `npm run build` and check for
TypeScript errors. Ensure newly created components include the `ports` array
added in the frontend store. When working with links, the backend API uses

### 6.8 API Error Handling
Endpoints that fetch a specific resource (e.g., `/api/v1/components/{component_id}`)
will return a `404 Not Found` error if the resource does not exist. The UI status
bar will surface these and other API communication errors.

The `/api/v1/ai/command` endpoint is rate-limited to **30 requests per minute**
using the `slowapi` library. The limiter is initialized in `backend/main.py` by
attaching it to `app.state` and registering the rate limit exception handler.

Links returned from the API now include `source_id` and `target_id` fields
referencing the connected components. Use the same flat structure when creating
a new link via `POST /api/v1/links/`.

Partial updates to a component should be sent via
`PATCH /api/v1/components/{component_id}`. Deleting a component returns a
`204 No Content` response on success.

### Common 4xx responses from AI endpoints

| status | meaning | typical fix |
|--------|---------|-------------|
| 409 | component/link already exists | change name or let AI pick auto-code |
| 422 | AI could not generate structured output | rephrase command or add more context |
| 429 | rate-limited by OpenAI | wait / upgrade quota |

### 6.9 UI-Backend Connection (CORS Errors)
If API requests fail with `CORS` errors in the browser console, ensure the backend allows the frontend's origin. The default development configuration permits the following common development URLs:

```
http://localhost:5173
http://127.0.0.1:5173
http://localhost:8082
http://127.0.0.1:8082
```

If running the frontend on a different host or port, update the `origins` list in `backend/main.py`. The CORS middleware is added via `app.add_middleware` during application setup.

### 🔄 Typical AI loop

1. **User**: "add solar panel / inverter / battery"
2. **User**: "link solar panel to inverter"
3. **User**: "remove battery" → component disappears
4. **User**: "optimise the layout" → nodes rearranged
5. **User**: "what is the bill of materials" → BoM table appears

### 6.10 Adding Components via Datasheets

1. **Upload a Datasheet** – Click the paperclip icon and select a PDF. It appears in the Component Library on the left.
   Uploaded files are persisted on the backend and automatically reloaded when you refresh the page.
2. **Drag from Library** – Drag the uploaded component from the library onto the canvas to create an instance.
3. **Drag onto Components Canvas** – Dropping a datasheet onto the Components view now triggers background parsing. A spinner shows progress until the Reviewer AI confirms the data, after which the split view opens with a form-based editor. Errors are surfaced inline.
4. **AI Assistant** – Alternatively say, "Add the SUN2000-150K-MG0.pdf datasheet to the project" and the assistant will place it for you.

---

## 7. Architecture & Design
```mermaid
graph TD
    subgraph Frontend
        A[React App]
        B[Engineering Canvas]
        C[Customer Project Wizard]
        D[Component Pack Studio]
        E[Admin Console]
    end
    subgraph Backend
        F[FastAPI]
        G[Workflow Engine]
        H[Compliance Engine]
        I[Datasheet Processor]
    end
    subgraph AI Services
        J[AI Models]
        K[Media Validation]
        L[Model Registry]
    end
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    F --> G
    F --> H
    F --> I
    G --> J
    H --> J
    I --> J
    J --> L
    K --> J
```

---

## 8. Contributing
- Fork the repository, create a branch, and submit pull requests.
- Run `./scripts/lint.sh && ./scripts/test.sh` before submitting.
- Add tests to maintain >90% coverage.
- Follow `AGENTS.md` for AI contributions.

---

## 9. License
BSD License (pending legal review).

---

## 10. Community & Support
- **Slack**: `#originflow-dev`.
- **Email**: `maintainers@originflow.dev`.
- **Docs**: [https://docs.originflow.dev](https://docs.originflow.dev).

Happy designing! 🚀
# <codex-marker>
frontend/package.json
frontend/src/services/api.ts
frontend/src/appStore.ts
frontend/src/components/Workspace.tsx
frontend/src/components/PropertiesPanel.tsx
frontend/src/components/LinkLayer.tsx
frontend/src/components/ChatPanel.tsx
frontend/src/components/ChatInput.tsx
backend/__init__.py
backend/api/__init__.py
backend/api/routes/components.py
backend/api/routes/links.py
backend/api/routes/ai.py
backend/agents/router_agent.py
backend/agents/component_agent.py
backend/config.py
backend/database/session.py
backend/models/component.py
backend/models/link.py
backend/schemas/component.py
backend/schemas/link.py
backend/schemas/ai.py
backend/main.py
setup.cfg
