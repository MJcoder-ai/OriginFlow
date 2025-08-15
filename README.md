# OriginFlow

> **Modular • AI-Powered • Standards-Compliant** – A scalable platform for engineering design, starting with a browser-based environment for creating schematics and bills-of-materials.

---

## 1. Overview

OriginFlow is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into standards-compliant schematics and bills-of-materials. It supports both engineers and non-technical users, offering features like drag-and-drop datasheets, AI auto-completion, and real-time compliance checks.

Recent updates introduce a **Multi-Domain Platform** with placeholder component support:
  - **Placeholder Component System**: Start designing with generic components before real datasheets are available
  - **Enhanced Dynamic Planner**: Placeholder-aware task generation with multi-domain support (PV, battery, monitoring)
  - **Component Selector Agent**: Intelligent replacement of placeholders with real parts based on requirements
  - **ODL Code View**: Live textual representation of designs with real-time updates
  - **Requirements Management**: Comprehensive form-based requirement collection and validation
  - **Version Control**: Complete graph versioning with patch history and revert capabilities
  - **Enhanced APIs**: 15+ new endpoints for ODL session management, component selection, and analysis
  - **Governance & Safety Policies**: Risk-based auto‑approval based on agent classifications and confidence scores, ensuring high‑risk actions always require human review
  - **Extended Multi‑Domain Support**: Battery and monitoring agents automatically design energy storage and telemetry systems, deepening the placeholder‑first multi‑domain framework
  - **Compliance & Rule Engine**: Enhanced rule engine with validation of installed wires and fuses; cross-layer validation agent now checks for unconnected components
  - **ADPF Integration**: All AI agents return results in a standard JSON envelope with meta-cognitive reasoning (`thought`), structured output and status.  See `backend/utils/adpf.py` for details.

### Planner and Domain Agents

OriginFlow now includes an **enhanced dynamic planner** that provides placeholder-aware task generation and multi-domain support. The planner analyzes graph state and generates contextual tasks:

**Core Tasks:**
1. `gather_requirements` – Collect design requirements (with placeholder design option)
2. `generate_design` – Create PV design using real components or placeholders
3. `generate_structural` – Add mounting systems (placeholder or real)
4. `generate_wiring` – Add cables and protection devices
5. `populate_real_components` – Replace placeholders with real components

**Domain-Specific Tasks:**
6. `generate_battery` – Design battery storage systems
7. `generate_monitoring` – Add system monitoring capabilities
8. `refine_validate` – Final optimization and validation

**Enhanced Domain Agents:**

* **PVDesignAgent** – Generates placeholder or real component designs based on availability
* **ComponentSelectorAgent** – Finds and ranks real components to replace placeholders
* **StructuralAgent** – Creates mounting systems with placeholder support
* **WiringAgent** – Designs electrical connections using placeholders or real components

**Key Workflow Innovation:**
- Start designing immediately with placeholder components
- Gradually replace placeholders as real component data becomes available
- Maintain design connectivity throughout the iterative process
- Support for mixed designs (real + placeholder components)

Each agent returns enhanced design cards with confidence scores, specifications, interactive actions, warnings, and recommendations.

### 🚀 **Current Status: Multi-Domain Platform (Phase 1 Complete)**
- ✅ **Core Design Platform**: Fully functional canvas, components, AI chat interface
- ✅ **20+ AI Agents**: PV design, component selection, structural, wiring, and domain agents  
- ✅ **Placeholder Component System**: 7 generic component types with intelligent replacement
- ✅ **Enhanced Dynamic Planner**: Context-aware task generation with multi-domain support
- ✅ **ODL Code View**: Live textual design representation with real-time updates
- ✅ **Requirements Management**: Comprehensive form-based requirement collection
- ✅ **Component Selection**: Intelligent candidate finding and ranking system
- ✅ **Learning System**: Confidence-driven autonomy with vector-based memory
- ✅ **Production Ready**: SQLite/PostgreSQL, robust error handling, type safety

### 🔮 **Roadmap: Enterprise Platform Vision**
- ⏳ **Phase 2** (6-12 months): Sales & procurement agents, workflow orchestration
- ⏳ **Phase 3** (12-18 months): Field operations, AR assistance, IoT integration  
- ⏳ **Phase 4** (18-24 months): Full lifecycle automation, predictive analytics

The platform is architected for enterprise scale but currently implements core engineering design functionality. See sections below for detailed current vs planned capabilities.

---

## 2. Key Features
- **Engineering Canvas**: A drag-and-drop interface for creating and editing schematics with AI-driven auto-completion, industry-standard naming, WebGL rendering, CRDT-based offline sync, and port-based connections between components. Links are created by dragging from an output port to an input port, with ports highlighting during the drag. Component dragging is separate from linking, so accidental moves are avoided. Connection lines now align precisely with each port for clearer diagrams.
- **Multi-Layer Canvas**: Switch between named layers (e.g., single-line, high-level) so complex designs stay organized. Each layer stores its own component positions.
  - **ODL Graph & Plan–Act Loop (New)**: Designs are now backed by the OriginFlow Design Language (ODL), a network‑graph representation of all components, connections and annotations. Each node corresponds to a physical or logical entity (panel, inverter, roof, sensor) and each edge captures a relation (electrical, mechanical, data). A new PlannerAgent decomposes your natural language commands into a sequence of high‑level tasks, which are displayed in the Plan Timeline and executed by specialised domain agents (PV design, wiring, structural, network and assemblies). These agents operate on the ODL graph via patches and return rich Design Cards summarising their suggestions. Session graphs are persisted so work survives restarts. The `/api/v1/odl/sessions` endpoint creates a new session (accepts optional client `session_id`) and `/api/v1/odl/{session_id}/act` applies patches, returning the updated `version`. This plan–act loop allows OriginFlow to evolve a design across layers and disciplines while giving you full visibility and control. The planner now emits stable task identifiers—`gather_requirements`, `generate_design`, `refine_validate`—and the PVDesignAgent performs a dedicated gather step that checks the component database for panels and inverters, prompting for missing datasheets or confirming readiness. The frontend preserves task status across messages so completed steps aren’t repeated. New endpoints let you update requirements mid‑session, undo or redo changes via versioned patches, and the PV agent sizes arrays and delegates structural and wiring refinements with confidence scoring. The orchestrator also parses numeric requirements like target power, available roof area and currency budgets directly from natural-language commands so downstream agents receive structured inputs automatically.
- **Interactive Layer Selector**: Use the layer selector in the toolbar to create and switch between named layers (e.g. Single‑Line, High‑Level, Electrical, Structural, Networking). New components automatically inherit the current layer, and their layer assignment is persisted. Layers allow different stakeholders to focus on the view relevant to them while sharing a single underlying model.

    - **Sub‑Assembly Generation**: Once a component is placed, you can expand it into its required sub‑assemblies. Select a component and click **Generate Sub‑Assembly** to populate the appropriate detail layer (electrical or structural) with brackets, rails, combiner boxes or other accessories based on **both dependency rules and nested sub‑elements** defined in the component library. The **DesignAssemblyAgent** looks up the component in the master database and returns the necessary ``addComponent`` actions for every required item and sub‑element, applying them automatically.

- **Detailed Layers**: Beyond the high‑level single‑line view, OriginFlow lets you toggle into *electrical detail* or *structural* layers. Electrical detail layers expose all physical ports on a component (e.g. multiple MPPT inputs and AC terminals on an inverter) so you can size strings and branch circuits correctly. Structural layers show mounting brackets, rails and roof attachments for PV systems. Each layer stores its own component positions and visibility, keeping complex designs organised without cluttering the main schematic.

  - **Deterministic Rule Engine & Wiring Agent**: A built‑in rule engine performs verifiable safety‑critical calculations such as wire sizing. Given a load and distance, it returns the correct gauge, cross‑section area, current, voltage drop and recommended fuse rating. The **WiringAgent** parses natural‑language requests like `size wiring for 5 kW over 20 m` and produces a detailed report, adding the recommended components directly to your design.

  - **AI‑Generated Connections**: The SystemDesignAgent now proposes both components *and* the links between them. When designing a solar PV system, for example, it will not only add the panels, inverter and battery but also suggest connecting each PV string to the inverter and the inverter to the battery. These suggestions use human‑readable names instead of opaque IDs and are applied automatically.

- **Real-Component Designs**: The SystemDesignAgent selects actual panels, inverters and batteries from the component library. If a required category is missing, it asks you to upload the datasheet and waits for the component to be added before proceeding.

- **Undo/Redo & Action History**: Every AI suggestion—component placement, link creation, wiring—is recorded in a history stack. Toolbar buttons let you undo or redo approved actions, giving you full control over the design iteration and the ability to experiment safely.

- **Customer Project Wizard**: A guided interface for non-technical users to plan projects with AI suggestions and cost estimation.
- **AI-Driven Datasheet Processing**: Asynchronous parsing pipeline with status tracking, Chain-of-Thought extraction and a Reviewer AI for higher accuracy.
- **Datasheet Library Augmentation**: When a PDF datasheet is parsed, the extracted metadata is automatically added to the component library—populating the part number, manufacturer, category (or a heuristic guess when omitted), electrical ratings, ports, dependencies, series names, per‑product variants and nested sub‑elements.  This ensures that future designs use *real* components from your library and reduces manual data entry.
- **Media Management**: Datasheet images are linked to their parent PDF via a `parent_asset_id`, so they no longer appear as standalone entries in the component library. Images are automatically extracted from uploaded datasheets using **pypdf** and, if they are in less common formats (e.g. JPEG 2000, TIFF, JBIG2 or raw bitmap), the parser converts them to JPEG before saving for broad browser compatibility. Images can also be uploaded manually. Exactly one image is always marked as the primary thumbnail at a time. Videos remain supported via manual upload, and all media can be validated by AI with Octopart API integration.
- **Standards Compliance Engine**: Real-time validation against industry standards (e.g., IEC 81346) with webhook-driven revalidation.
- **Workflow Orchestration**: Self-hosted Temporal.io for reliable execution of complex workflows, including Saga Pattern for rollbacks.
- **Feedback Logging**: Each AI action is recorded, enabling confidence modeling and audit trails.
- **Enterprise Settings Console**: Tabbed settings UI that surfaces Profile, Organization, Roles & Permissions, Memory and Traceability sections based on user permissions.
- **Memory & Traceability APIs**: Endpoints `/me`, `/memory`, `/traces`, `/traces/{trace_id}` expose user profiles, stored memories and tamper-evident trace events.
- **Variant Splitting & Memory Logging**: Multi‑option datasheets are automatically split into individual variant records, ensuring each product variant can be selected separately. Every AI command is recorded as a memory entry summarising the command and the actions taken, and linked to the conversation’s trace ID for auditing.
- **Confidence-Driven Autonomy & Advanced Learning**: The **LearningAgent** no longer relies solely on action type when estimating whether a suggestion will succeed. It analyses the domain of each command (e.g. solar PV, HVAC or pumping) and computes separate approval rates for each domain and action type using the feedback log. At runtime, it also inspects action payloads to infer the domain when computing confidence scores. These domain-aware scores let OriginFlow apply routine changes automatically while flagging low-confidence tasks as blocked. As more feedback is gathered, the confidence model retrains and gradually raises the autonomy threshold in mature domains. See `backend/agents/learning_agent.py` for implementation details and `backend/models/ai_action_log.py` for the logging schema.
- **Extensibility**: Plug-in framework for components, AI models, and workflows via Component Pack Studio and marketplace.
- **Observability**: Grafana dashboards, OpenTelemetry traces, and Workflow Visibility Dashboard for monitoring.
- **Chat Sidebar**: Dedicated panel for collaborating with the AI assistant. This sidebar has evolved into a mission‑control centre: it now displays a high‑level Plan Timeline at the top of the chat history, uses rich Design Cards to present AI suggestions, and includes a Quick‑Action Bar and Mode Selector above the input. Conversation history persists across sessions, and the AI proactively notifies you when required components are missing or guides you to upload datasheets or choose alternatives.
    - **Plan Timeline**: A dynamic timeline summarises the AI’s tasks (e.g. selecting panels, sizing wiring) with status icons that indicate whether each task is pending, in‑progress, complete or blocked. Tasks are generated by new planning endpoints (e.g. `POST /api/v1/ai/plan` for legacy sessions or `POST /api/v1/odl/{session_id}/plan` for ODL‑based projects) that decompose your command into high‑level steps. Each task is executed automatically via `/api/v1/odl/{session_id}/act`, applying patches to the canvas and displaying a Design Card. Timeline entries remain clickable to re-run steps or adjust statuses. The timeline collapses away when there are no active tasks.
  - **Design Cards**: When the AI proposes a component, bill of materials or calculation, it presents a full‑width card with a title, description, optional image, specification table and buttons to accept or swap alternatives.
  - **Quick Actions & Modes**: A horizontal row of buttons above the input offers one‑click commands like “Generate BOM” or “Run Performance Analysis”, and a drop‑down lets you toggle between Design, Analyze, Manual and Business modes. These settings adjust the AI’s capabilities and steer prompt interpretation.
  - **Voice Mode Chat Input**: Click the microphone icon to dictate messages. A continuous conversation mode lets the mic automatically re-engage after each AI reply. Say "stop listening" to end.
  - **AI Processing Indicator**: While Echo is thinking, a subtle spinner appears at the bottom of the chat history.
  - **Datasheet Upload Button**: Use the paperclip icon next to the mic to upload PDF datasheets into the Component Library. A spinner and badge show progress while files upload.
- **Multi-Line Chat Input**: Compose longer messages in a textarea that auto-resizes as you type.
- **Component Deletion by Name**: Remove components via the AI assistant or UI by referencing the component's name.
 - **Enhanced Component Library**: A compact filter and search bar appears just under the library heading.  Icons allow you to toggle an inline search input or a filter panel without stealing screen real estate.  When you activate the search, the “Component Library” label collapses and the search field expands to fill the available width of the sidebar.  Components are automatically prioritised by the AI to surface the most relevant items first, but searching or filtering overrides the ordering.  Each component card maintains its size but now reserves a small area for a thumbnail image when extracted from the datasheet.
- **AI Agents (Phase 1)**: Core design agents for engineering workflows. **18 agents implemented** of the 42 planned in AGENT_TAXONOMY.md:

   **✅ Implemented Core Agents:**
   - **SystemDesignAgent** – High-level design using only library components, prompting for datasheets when parts are missing
   - **WiringAgent** – Uses deterministic rule engine for wire sizing, fuse selection, and safety calculations
   - **PerformanceAgent** – Quick estimates of system output using heuristic formulas (Phase 1: basic calculations)
   - **FinancialAgent** – Cost estimation using per-kW pricing heuristics (Phase 1: simple calculations)
   - **SourcingAgent** – Searches component library for alternatives (Phase 1: local search only)
   - **CrossLayerValidationAgent** – Basic validation with manual check reminders (Phase 1: stub implementation)
   - **LearningAgent** – Domain-aware confidence scoring with automatic execution for high-confidence actions
   - **ComponentAgent**, **InventoryAgent**, **BomAgent**, **LinkAgent**, **LayoutAgent** – Core CRUD operations
   - **AuditorAgent**, **DatasheetFetchAgent**, **DesignAssemblyAgent**, **KnowledgeManagementAgent** – Support functions

   **⏳ Future Phases (24 agents planned):**
   - Phase 2: Sales & procurement agents (lead discovery, price finding, purchase orders)
   - Phase 3: Field operations (AR assistance, commissioning, quality audit)
   - Phase 4: After-sales (support, warranty, predictive maintenance)

   Current orchestration uses simple routing. **Event-driven orchestration with Temporal.io workflows planned for Phase 2.**

- **Component Master Database**: Central inventory of manufacturer parts and specifications.
- **Hierarchical Component Schema**: Components can represent entire product families with variants, shared documents, and **nested sub‑components**. Each record can define ports (DC, AC, grounding, communication), dependencies (e.g. required mounting rails or brackets) and layer affinities, plus a `series_name` and an array of `variants` extracted from multi‑option datasheets. This richness allows the AI to “explode” a single‑line component into detailed assemblies on electrical and structural layers while keeping inventory management efficient.

    The schema now includes a ``sub_elements`` array so a component can contain its own children (e.g., a solar panel with brackets and rails).  Additional fields ``ports``, ``dependencies`` and ``layer_affinity`` describe physical connection points, required or optional accessories, and the canvas layers where each element belongs.  New ``series_name`` and ``variants`` columns capture product families and per‑option attributes from multi‑product datasheets.  See `backend/models/component_master.py` for details.  Alembic migrations add these columns to the database.
- **Performance Benchmarks**:
  | **Nodes** | **CPU (cores)** | **RAM (GB)** |
  |-----------|-----------------|--------------|
  | 100       | 2               | 4            |
  | 1000      | 4               | 8            |
  | 2000      | 8               | 16           |
### 2.5 AI Agents (Phase 1 Implementation)
OriginFlow uses AI agents for engineering design tasks. **Current Phase 1 status:**

**✅ Implemented (18 agents):**
- **SystemDesignAgent**: High-level design using only library components; prompts for datasheets when parts are missing
- **WiringAgent**: Deterministic wire sizing and safety calculations  
- **PerformanceAgent**: Basic performance estimation with heuristic formulas
- **FinancialAgent**: Cost estimation using per-kW pricing
- **ComponentAgent**: Component lifecycle management
- **Plus 13 supporting agents** for inventory, BOM, links, layout, auditing, etc.

**⏳ Planned (24 agents):** Marketing, sales, procurement, logistics, field ops, after-sales
- See AGENT_TAXONOMY.md for complete roadmap
- ENGINEERING_PLAYBOOK.md for development guidelines

**Current Limitation**: Simple router-based orchestration. Event-driven workflows with Temporal.io planned for Phase 2.

### 2.6 Feedback Vector Logging & Confidence
OriginFlow logs every AI action along with its outcome. The
v2 feedback endpoint (`/api/v1/ai/log-feedback-v2`) anonymises prompts
and design context, embeds them and stores the vectors in a configurable
vector store. These vectors are retrieved by the `LearningAgent` and the
`ReferenceConfidenceService` to compute context-aware confidence scores
for future actions.

Validation actions are informational only and are never auto-applied.

The vector store backend is selected via environment variables:

- `VECTOR_BACKEND` – `qdrant` (default) or `chroma`
- `QDRANT_HOST`, `QDRANT_COLLECTION`, `VECTOR_SIZE`
- `CHROMA_COLLECTION`, `CHROMA_PERSIST_DIR`

See `docs/feedback_logging.md` for more details on anonymisation,
embedding and retrieval-based confidence.

---

## 3. Supported Technologies (Phase 1)

**✅ Current Implementation:**
- **Frontend**: React 18.2, TypeScript 5.3, react-flow 11.10, Tailwind CSS 3.4, Zustand 4.5, @dnd-kit/core 6.0
- **Backend**: FastAPI 0.109, Python 3.11, SQLite (default) or PostgreSQL 16
- **AI/ML**: OpenAI GPT-4o-mini, sentence-transformers/all-MiniLM-L6-v2, Qdrant/Chroma vector stores
- **Data Processing**: PDF parsing (pdfplumber, PyMuPDF), table extraction (basic)
- **File Storage**: Local filesystem with static file serving

**⏳ Planned Enhancements:**
- **Advanced AI**: LlamaIndex, spaCy, YOLOv8, OpenCV, multi-modal processing
- **Workflow**: Temporal.io workflows, event-driven architecture
- **Infrastructure**: Redis caching, S3-compatible storage, Kafka messaging
- **Observability**: Grafana dashboards, OpenTelemetry traces, Loki logging
- **Authentication**: Supabase integration, role-based access
- **Offline**: IndexedDB via Dexie.js for offline-first capabilities

---

## 4. Getting Started

### 4.1 Prerequisites (Phase 1)
**Required:**
- Node.js ≥18, npm ≥9
- Python ≥3.11, Poetry ≥1.8
- SQLite (default) or PostgreSQL 16
- OpenAI API key

**Optional (for enhanced features):**
- Redis 7.2 (for caching)
- Qdrant or Chroma (for vector storage, falls back to NoOp)

**Future Phases:**
- Kafka, HashiCorp Vault, Temporal.io (Phase 2+)

### 4.2 Installation (Phase 1 - Simplified)
```bash
# 1. Clone and install dependencies
git clone https://github.com/your-org/OriginFlow.git
cd OriginFlow
poetry install --with dev
npm install

# 2. Configure environment  
cp .env.example .env
# Edit .env to add OPENAI_API_KEY (required)
# DATABASE_URL defaults to SQLite if not set

# 3. Initialize database
poetry run alembic upgrade head

# 4. Start services
poetry run uvicorn backend.main:app --reload --host 0.0.0.0
npm --prefix frontend run dev -- --port 5173
```

**Optional: Enhanced Setup**
```bash
# For vector storage (enhanced learning)
docker run -p 6333:6333 qdrant/qdrant

# For PostgreSQL (production)  
docker compose up -d postgres
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

### AI Commands (Phase 1 - Currently Available)

**✅ Fully Implemented:**
* **size wiring for 5 kW over 20 m** – Deterministic wire gauge and fuse sizing using rule engine
* **remove _{name}_** – Deletes components by name
* **what is the bill of materials** – Shows modal with unique part list
* **organise / optimise layout** – Neatly re-positions nodes

**✅ Basic Implementation:**
* **design a 5 kW solar system** – Suggests major components (pattern matching + hardcoded components)
* **find panels 400** – Searches the component library (local search only)
* **analyse / validate** – Basic design audit with manual check reminders
* **estimate system performance** – Returns heuristic performance estimates (not real simulation)
* **datasheet for ABC123** – Fetches and parses datasheets (basic extraction, no OCR fallback)

**⏳ Enhanced Features Planned:**
- External API integration for pricing and performance
- Advanced RAG-based knowledge queries  
- Real-time simulation and optimization
- Multi-modal datasheet processing

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

### 6.11 Dynamic ODL Plan–Act System

OriginFlow now features a **dynamic, state-aware planning system** that intelligently adapts to the current design state and user requirements. The system replaces static planning with contextual task generation.

#### Key Features

- **Dynamic Task Generation**: Tasks are generated based on current graph state, requirements completeness, and component availability
- **Enhanced Design Cards**: Rich cards with confidence scores, specifications, interactive actions, and recommendations
- **Automatic Plan Refresh**: Plans update automatically after task completion
- **Version Control**: Complete undo/redo with diff tracking and revert capabilities
- **Graph State Analysis**: Comprehensive graph summarization with warnings and component analysis

#### Core Endpoints

**Create a session:**
```bash
curl -X POST http://localhost:8000/api/v1/odl/sessions \
     -H "Content-Type: application/json" \
     -d '{"session_id":"my-session-123"}'
```

**Get dynamic plan based on current state:**
```bash
curl -X POST http://localhost:8000/api/v1/odl/my-session-123/plan \
     -H "Content-Type: application/json" \
     -d '{"command":"design 5 kW pv system"}'
```

**Execute task with enhanced response:**
```bash
curl -X POST http://localhost:8000/api/v1/odl/my-session-123/act-enhanced \
     -H "Content-Type: application/json" \
     -d '{"task_id":"generate_design","graph_version":2}'
```

#### New State Management Endpoints

**Check requirements status:**
```bash
curl -X GET http://localhost:8000/api/v1/odl/requirements/my-session-123/status
```

**Get version differences:**
```bash
curl -X GET "http://localhost:8000/api/v1/odl/versions/my-session-123/diff?from_version=0&to_version=2"
```

**Revert to previous version:**
```bash
curl -X POST http://localhost:8000/api/v1/odl/versions/my-session-123/revert \
     -H "Content-Type: application/json" \
     -d '{"target_version":1}'
```

**View agent registry:**
```bash
curl -X GET http://localhost:8000/api/v1/odl/registry/tasks
```

#### Dynamic Planning Logic

The planner now intelligently decides task sequences:

1. **gather_requirements**: Emitted when user inputs or component datasheets are missing
2. **generate_design**: Only when no panels/inverters exist AND requirements are complete
3. **generate_structural**: After design exists but mounting is missing  
4. **generate_wiring**: After design exists but electrical connections are missing
5. **refine_validate**: Final validation step when design components exist

#### Enhanced Design Cards

Tasks now return rich design cards with:
- **Confidence scores** (0.0-1.0) based on AI learning
- **Specifications** with units and individual confidence ratings
- **Interactive actions** (Accept, See Alternatives, Modify Requirements)
- **Warnings** for design issues or low confidence
- **Recommendations** for next steps or improvements

#### Task Dependencies and Validation

The system tracks task prerequisites and validates execution order:
```bash
curl -X POST http://localhost:8000/api/v1/odl/registry/validate-sequence \
     -H "Content-Type: application/json" \
     -d '["gather_requirements", "generate_design", "generate_structural"]'
```
If the provided `version` is out of date the endpoint returns **409 Conflict**.
Clients should refresh the graph (e.g. via `/versions/{session_id}/diff`),
update their plan and retry the task.

- Update requirements mid-session to unblock `generate_design`:

```bash
curl -X POST http://localhost:8000/api/v1/requirements/my-session-123 \
     -H "Content-Type: application/json" \
     -d '{"target_power":5,"roof_area":30,"budget":10000,"brand":"Any"}'
```

- Inspect patch history and revert:

```bash
curl "http://localhost:8000/api/v1/versions/my-session-123/diff?from_version=0&to_version=5"
curl -X POST http://localhost:8000/api/v1/versions/my-session-123/revert \
     -H "Content-Type: application/json" \
     -d '{"target_version":3}'
```

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

## 7. Architecture & Design (Phase 1 Current + Future Vision)

### 7.1 Current Phase 1 Architecture
```mermaid
graph TD
    subgraph Frontend
        A[React App]
        B[Engineering Canvas]
        C[Chat Interface]
    end
    subgraph Backend
        F[FastAPI]
        I[Datasheet Processor]
        Agents[AI Agents - 18 implemented]
        Router[RouterAgent]
        Learning[LearningAgent]
    end
    subgraph AI Services
        J[OpenAI GPT-4o-mini]
        Vector[Vector Store - Qdrant/Chroma]
        Embed[Embedding Service]
    end
    A --> F
    B --> F
    C --> F
    F --> Router
    Router --> Agents
    Agents --> Learning
    Learning --> Vector
    Learning --> Embed
    F --> I
    I --> J
    Agents --> J
```

### 7.2 Planned Full Architecture (Phase 2-4)
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
        G[Temporal Workflows]
        H[Compliance Engine]
        I[Datasheet Processor]
        Agents[AI Agents - 42 planned]
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
backend/init.py
backend/api/init.py
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

