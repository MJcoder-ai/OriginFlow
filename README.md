# OriginFlow

> **Modular • AI-Powered • Standards-Compliant** – A scalable platform for engineering design, starting with a browser-based environment for creating schematics and bills-of-materials.

---

## 1. Overview
OriginFlow is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users, offering features like drag-and-drop datasheets, AI auto-completion, and real-time compliance checks. The platform is built to be modular, scalable, and extensible, with a focus on reliability and user experience. Now with integrated AI agents for end-to-end automation (design, sales, support).

---

## 2. Key Features
- **Engineering Canvas**: A drag-and-drop interface for creating and editing schematics with AI-driven auto-completion, industry-standard naming, WebGL rendering, CRDT-based offline sync, and port-based connections between components. Links are created by dragging from an output port to an input port, with ports highlighting during the drag. Component dragging is separate from linking, so accidental moves are avoided. Connection lines now align precisely with each port for clearer diagrams.
- **Multi-Layer Canvas**: Switch between named layers (e.g., single-line, high-level) so complex designs stay organized. Each layer stores its own component positions.
- **Interactive Layer Selector**: Use the layer selector in the toolbar to create and switch between named layers (e.g. Single‑Line, High‑Level, Electrical, Structural, Networking). New components automatically inherit the current layer, and their layer assignment is persisted. Layers allow different stakeholders to focus on the view relevant to them while sharing a single underlying model.

   - **Sub‑Assembly Generation**: Once a component is placed, you can expand it into its required sub‑assemblies. Select a component and click **Generate Sub‑Assembly** to populate the appropriate detail layer (electrical or structural) with brackets, rails, combiner boxes or other accessories based on **both dependency rules and nested sub‑elements** defined in the component library. The **DesignAssemblyAgent** looks up the component in the master database and returns the necessary ``addComponent`` actions for every required item and sub‑element, which appear in the interactive checklist for your approval.

- **Detailed Layers**: Beyond the high‑level single‑line view, OriginFlow lets you toggle into *electrical detail* or *structural* layers. Electrical detail layers expose all physical ports on a component (e.g. multiple MPPT inputs and AC terminals on an inverter) so you can size strings and branch circuits correctly. Structural layers show mounting brackets, rails and roof attachments for PV systems. Each layer stores its own component positions and visibility, keeping complex designs organised without cluttering the main schematic.

- **Deterministic Rule Engine & Wiring Agent**: A built‑in rule engine performs verifiable safety‑critical calculations such as wire sizing. Given a load and distance, it returns the correct gauge, cross‑section area, current, voltage drop and recommended fuse rating. The **WiringAgent** parses natural‑language requests like `size wiring for 5 kW over 20 m` and produces a detailed report. These suggestions appear in the interactive checklist for your approval.

- **AI‑Generated Connections**: The SystemDesignAgent now proposes both components *and* the links between them. When designing a solar PV system, for example, it will not only add the panels, inverter and battery but also suggest connecting each PV string to the inverter and the inverter to the battery. These suggestions use human‑readable names instead of opaque IDs and are queued in the checklist for your approval.

- **Undo/Redo & Action History**: Every AI suggestion—component placement, link creation, wiring—is recorded in a history stack. Toolbar buttons let you undo or redo approved actions, giving you full control over the design iteration and the ability to experiment safely.

- **Customer Project Wizard**: A guided interface for non-technical users to plan projects with AI suggestions and cost estimation.
- **AI-Driven Datasheet Processing**: Asynchronous parsing pipeline with status tracking, Chain-of-Thought extraction and a Reviewer AI for higher accuracy.
- **Media Management**: Upload or capture component images/videos, validated by AI with Octopart API integration.
- **Standards Compliance Engine**: Real-time validation against industry standards (e.g., IEC 81346) with webhook-driven revalidation.
- **Workflow Orchestration**: Self-hosted Temporal.io for reliable execution of complex workflows, including Saga Pattern for rollbacks.
- **Interactive AI Checklist**: Review and approve AI-suggested actions before they modify your design.
- **Feedback Logging**: Each approval or rejection is recorded, enabling confidence modeling and audit trails.
- **Confidence-Driven Autonomy & Advanced Learning**: The **LearningAgent** no longer relies solely on action type when estimating whether a user will approve a suggestion.  It now analyses the domain of the command (e.g. solar PV, HVAC or pumping) and computes separate approval rates for each domain and action type using the feedback log.  At runtime, it also inspects the payload of each action to guess the domain when computing confidence scores.  These domain-aware confidence scores allow OriginFlow to automatically apply routine changes in areas where the AI has a strong track record, while still queuing novel or complex tasks for human approval.  As more feedback is gathered, the confidence model retrains and gradually raises the autonomy threshold in mature domains.  See `backend/agents/learning_agent.py` for implementation details and `backend/models/ai_action_log.py` for the logging schema.
- **Extensibility**: Plug-in framework for components, AI models, and workflows via Component Pack Studio and marketplace.
- **Observability**: Grafana dashboards, OpenTelemetry traces, and Workflow Visibility Dashboard for monitoring.
- **Chat Sidebar**: Dedicated panel for collaborating with the AI assistant. Includes voice mode input and persists conversation history.
  - **Voice Mode Chat Input**: Click the microphone icon to dictate messages. A continuous conversation mode lets the mic automatically re-engage after each AI reply. Say "stop listening" to end.
  - **AI Processing Indicator**: While Echo is thinking, a subtle spinner appears at the bottom of the chat history.
  - **Datasheet Upload Button**: Use the paperclip icon next to the mic to upload PDF datasheets into the Component Library. A spinner and badge show progress while files upload.
- **Multi-Line Chat Input**: Compose longer messages in a textarea that auto-resizes as you type.
- **Component Deletion by Name**: Remove components via the AI assistant or UI by referencing the component's name.
- **AI Agents**: Modular agents for marketing, design, procurement, and more (see AGENT_TAXONOMY.md).  Recent additions include:

   - **WiringAgent** – uses the deterministic rule engine to size wires, select fuses and ferrules, and generate detailed wiring reports from natural‑language requests.
   - **PerformanceAgent** – provides quick estimates of system output (e.g. expected annual kWh) and derating factors. Use the chat command `estimate system performance` to get a stub report.
   - **FinancialAgent** – aggregates component costs and updates live totals in the status bar. In future phases it will query supplier APIs for real‑time pricing and lead times.
   - **Cross‑Layer Validation Agent (Beta)**: To help ensure completeness across layers, the new CrossLayerValidationAgent will eventually verify that all ports are connected and that required sub‑assemblies (brackets, rails, combiner boxes) have been added on their respective detail layers.  In this beta release it returns a reminder to perform a manual check, but upcoming versions will parse the design snapshot and highlight missing connections automatically.
   - **Interactive Checklist Handler** – queues AI actions for human approval, ensuring that only high‑confidence suggestions are executed automatically.

   These agents are orchestrated by the **SystemDesignAgent**, which decomposes a user’s request into a sequence of tasks: selecting components, sizing wiring, connecting ports, estimating cost and performance, and generating reports. See `backend/agents/system_design_agent.py` for details.

- **Component Master Database**: Central inventory of manufacturer parts and specifications.
- **Hierarchical Component Schema**: Components can represent entire product families with variants, shared documents, and **nested sub‑components**. Each record can define ports (DC, AC, grounding, communication), dependencies (e.g. required mounting rails or brackets) and layer affinities. This richness allows the AI to “explode” a single‑line component into detailed assemblies on electrical and structural layers while keeping inventory management efficient.

    The schema now includes a ``sub_elements`` array so a component can contain its own children (e.g., a solar panel with brackets and rails).  Additional fields ``ports``, ``dependencies`` and ``layer_affinity`` describe physical connection points, required or optional accessories, and the canvas layers where each element belongs.  See `backend/models/component_master.py` for details.  Alembic migrations add these columns to the database.
- **Performance Benchmarks**:
  | **Nodes** | **CPU (cores)** | **RAM (GB)** |
  |-----------|-----------------|--------------|
  | 100       | 2               | 4            |
  | 1000      | 4               | 8            |
  | 2000      | 8               | 16           |
### 2.5 AI Agents
OriginFlow uses AI agents for non-physical tasks across the lifecycle. Examples:
- SystemDesignAgent: Orchestrates schematics and BOMs.
- LeadDiscoveryAgent: Finds prospects via web/X search.

See AGENT_TAXONOMY.md for the full list; ENGINEERING_PLAYBOOK.md for building/extending agents.

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

### 4.4 AI Agent Development
Define Spec Card in ENGINEERING_PLAYBOOK.md.
Implement in backend/agents/ (e.g., inherit from AgentInterface).
Register in backend/agents/init.py.
Test with pytest backend/agents/.
Example (SystemDesignAgent stub):

```python
from backend.agents.base_agent import AgentInterface

class SystemDesignAgent(AgentInterface):
    def execute(self, input: dict) -> dict:
        return {"design": "Generated schematic"}
```
The UI calls agents via /api/agents/execute.

### 4.5 UI Development
```bash
cd frontend
npm install
npm run dev
```

The UI uses `lucide-react` for icons. Run `npm install` after pulling updates to ensure the package is installed.

The dev server expects `index.html` in the frontend project root. Ensure
`@vitejs/plugin-react` is listed in `devDependencies`.

Layout dimensions for the sidebar and sub‑navigation are now managed via
`UIContext` in the frontend. The sidebar width collapses between `250px` and
`64px` while the optional sub‑navigation row can be toggled from the header.
The sidebar collapse control lives in the header menu, and the sidebar itself
shows a persistent logo even when collapsed. The status bar is fixed to the
bottom of the viewport.

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
- `USE_RULE_BASED`: Enable regex-based parsing.
- `USE_TABLE_EXTRACTION`: Extract tables using a multi-step pipeline
  (Camelot, Tabula and pdfplumber).
- `USE_AI_EXTRACTION`: Use AI to parse datasheet text and tables.
- `USE_OCR_FALLBACK`: Run OCR if initial text extraction fails.

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

### Updating the schema
If you add or modify any SQLAlchemy models, always generate a new
Alembic migration to keep the database schema in sync. Run:

```bash
alembic revision --autogenerate -m "<your message>"
alembic upgrade head
```
Failure to generate migrations can lead to runtime errors such as
"no such column" when the application queries the database.

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

### 🧠 Design Pattern Knowledge Base

Save and query reusable design embeddings:

```bash
# Persist a design embedding
curl -X POST http://localhost:8000/api/v1/design_vectors/ \
     -H "Content-Type: application/json" \
     -d '{"name":"residential_template","embedding":[0.01,0.02,0.03]}'

# Search for similar designs
curl -X POST http://localhost:8000/api/v1/design_vectors/search \
     -H "Content-Type: application/json" \
     -d '{"embedding":[0.01,0.02,0.03],"top_k":3}'
```

### Resetting the Component Master Database

During development you may need to remove erroneous entries from the
`component_master` table and rebuild the component library.  Use the
`delete_by_part_number` helper on `ComponentDBService` to remove a specific
part number while leaving the rest of the data intact.  To reset the table:

1. Ensure migrations are up to date:
   ```bash
   poetry run alembic upgrade head
   ```
2. Use the following script to delete all existing component records:
   ```python
   import asyncio
   from backend.services.component_db_service import ComponentDBService
   from backend.database.session import SessionMaker

   async def reset_db():
       async with SessionMaker() as session:
           svc = ComponentDBService(session)
           deleted = await svc.delete_by_part_number("ABC123")
           print(f"Deleted {deleted} component master records with part number ABC123")

   asyncio.run(reset_db())
   ```
3. Seed the database with fresh components using `bulk_create` or `create`.  See
   the PRD for recommended attributes.

### New AI commands

* **remove _{name}_** – deletes by name.
* **analyse / validate** – full snapshot audit.
* **what is the bill of materials** – shows modal with unique part list.
* **organise / optimise layout** – neatly re-positions nodes.
* **design a 5 kW solar system** – suggests major components.
* **find panels 400** – searches the inventory database.
* **datasheet for ABC123** – fetches and parses a datasheet (stub).
* **size wiring for 5 kW over 20 m** – deterministic wire gauge and fuse sizing.
* **estimate system performance** – returns a stub performance report.

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
   Uploaded files are persisted on the backend and automatically reloaded when you refresh the page. A badge shows how many uploads are still in progress.
2. **Drag from Library** – Drag the uploaded component from the library onto the canvas to create an instance.
3. **Manual Parsing** – Uploading no longer parses the PDF automatically. Drag the datasheet onto the canvas or click the "Parse" link in the library to start analysis. The UI polls the file status until parsing finishes, then opens the split view.
4. **AI Assistant** – Alternatively say, "Add the SUN2000-150K-MG0.pdf datasheet to the project" and the assistant will place it for you.
5. **Review & Confirm** – The split view includes a Save button and a "Confirm & Close" action. The chat history and input remain visible in the Properties panel on the right so you can ask questions while editing.
6. **In-Canvas Split View** – The datasheet view now opens directly inside the Components workspace, so no separate overlay element is required.
7. **Optional Tables** – If no tables are detected, the parsed payload may omit the `tables` field entirely. Treat this as a normal condition.
### 6.11 Invoking an AI Agent
```python
from backend.agents.orchestrator import OrchestratorAgent

orchestrator = OrchestratorAgent()
result = orchestrator.execute({"command": "Design 5kW PV system"})
```


### 6.12 PDF Viewer Errors
If the PDF viewer reports "Failed to load PDF" in the UI:
1. Confirm the backend is running on the URL configured in `VITE_API_URL`.
2. Ensure the backend created `backend/static/uploads` and is serving `/static` files. The directory is created at startup relative to `backend/main.py`.
3. Verify the file preview loads from `http://<backend-host>/api/v1/files/{asset_id}/file`.
4. Check that `frontend/src/main.tsx` configures the PDF.js worker from the local `pdfjs-dist` package. Using a CDN can trigger CORS errors.
5. Ensure `react-pdf` styles are imported from `react-pdf/dist/Page/*.css` rather than the nonexistent `dist/esm` path.

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
        Agents[AI Agents]
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
    F --> Agents
    Agents --> Orchestrator[BusinessOrchestratorAgent]
    Orchestrator --> SystemDesign[SystemDesignAgent]
    Orchestrator --> LeadGen[LeadDiscoveryAgent]
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
frontend/src/components/ChatInputArea.tsx
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

