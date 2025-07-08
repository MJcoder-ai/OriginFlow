# OriginFlow

> **Modular • AI-Powered • Standards-Compliant** – A scalable platform for engineering design, starting with a browser-based environment for creating schematics and bills-of-materials.

---

## 1. Overview
`OriginFlow` is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into fully-connected, standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users, offering features like drag-and-drop datasheets, AI auto-completion, and real-time compliance checks. The platform is built to be modular, scalable, and extensible, with a focus on reliability and user experience.

---

## 2. Key Features
- **Engineering Canvas**: A drag-and-drop interface for creating and editing schematics with AI-driven auto-completion, industry-standard naming, WebGL rendering, CRDT-based offline sync, and port-based connections between components. Links are created by dragging from an output port to an input port, with ports highlighting during the drag. Component dragging is separate from linking, so accidental moves are avoided. Connection lines now align precisely with each port for clearer diagrams.
- **Customer Project Wizard**: A guided interface for non-technical users to plan projects with AI suggestions and cost estimation.
- **AI-Driven Datasheet Processing**: Extracts and validates data from uploaded datasheets with multi-agent validation and error fallbacks.
- **Media Management**: Upload or capture component images/videos, validated by AI with Octopart API integration.
- **Standards Compliance Engine**: Real-time validation against industry standards (e.g., IEC 81346) with webhook-driven revalidation.
- **Workflow Orchestration**: Self-hosted Temporal.io for reliable execution of complex workflows, including Saga Pattern for rollbacks.
- **Extensibility**: Plug-in framework for components, AI models, and workflows via Component Pack Studio and marketplace.
- **Observability**: Grafana dashboards, OpenTelemetry traces, and Workflow Visibility Dashboard for monitoring.
- **Properties Panel with AI Chat**: Manage components via a drag-and-drop palette, edit selected component properties, and collaborate with an AI assistant.
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
- **AI Services**: pgvector 0.5, LlamaIndex, spaCy, sentence-transformers/all-MiniLM-L6-v2, YOLOv8, OpenCV, MLMD 0.2
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
- `DATABASE_URL`: URL for PostgreSQL connection.
- `TEMPORAL_HOST`: Host for self-hosted Temporal.io.

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

If the application serves an outdated build, run `npm run build` and check for
TypeScript errors. Ensure newly created components include the `ports` array
added in the frontend store. When working with links, the backend API uses

### 6.8 API Error Handling
Endpoints that fetch a specific resource (e.g., `/api/v1/components/{component_id}`)
will return a `404 Not Found` error if the resource does not exist. The UI status
bar will surface these and other API communication errors.

`source_id` and `target_id` fields, so convert them to the `source` and
`target` objects expected by the UI.

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
backend/__init__.py
backend/api/__init__.py
backend/api/endpoints.py
backend/models/__init__.py
backend/models/data_models.py
backend/database.py
backend/schemas.py
backend/main.py
setup.cfg
