# 🤖 AGENTS.md for OriginFlow

*This guide is for coding AIs (e.g., OpenAI Codex, GitHub Copilot) that auto-generate or refactor code in the `OriginFlow` repository. It outlines conventions, extension points, and safety rails for effective contributions without human micro-oversight. Updated July 28, 2025: Expanded for AI agent integration, including playbook references, taxonomy, and LLM-specific guidelines.*

> **Golden Rule:** *Never* break public contracts. Create a v2 interface and mark v1 as deprecated if changes are needed.

---

## 1. Project Topology

The `OriginFlow` repository is a browser-based, AI-powered design environment that converts rough engineering sketches and customer inputs into standards-compliant schematics and bills-of-materials. It separates frontend, backend, AI services, and shared utilities for maintainability. For AI agents, see new backend/agents/ dir for orchestration and tools.
OriginFlow/
├── .env.example
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── Dockerfile
├── requirements.txt
├── scripts/
│   ├── deploy.sh
│   ├── test.sh
│   ├── lint.sh
├── docs/
│   ├── api/
│   ├── guides/
│   │   ├── setup.md
│   │   ├── new_component.md
│   │   ├── new_workflow.md
│   │   └── troubleshooting.md
│   └── prd/
│       └── OriginFlow_PRD_v1.4.1.md
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── cd.yml
│   └── dependabot.yml
├── frontend/
│   ├── components/
│   │   ├── EngineeringCanvas.tsx
│   │   ├── ProjectWizard.tsx
│   │   ├── ComponentPackStudio.tsx
│   │   ├── AdminConsole.tsx
│   │   └── WorkflowDiffViewer.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   └── Dashboard.tsx
│   ├── utils/
│   │   ├── state.ts
│   │   └── telemetry.ts
│   └── tests/
│       ├── unit/
│       └── integration/
├── backend/
│   ├── api/
│   │   ├── endpoints.py
│   │   ├── compliance.py
│   │   ├── workflows.py
│   │   ├── media.py
│   │   └── model_registry.py
│   ├── services/
│   │   ├── workflow_engine.py
│   │   ├── compliance.py
│   │   ├── datasheet_processor.py
│   │   ├── naming_engine.py
│   │   └── audit.py
│   ├── models/
│   │   ├── data_models.py
│   │   └── migrations/
│   └── tests/
│       ├── unit/
│       └── integration/
├── ai_services/
│   ├── models/
│   │   ├── vision.py
│   │   ├── nlp.py
│   │   └── model_registry.py
│   ├── utils/
│   │   ├── validation.py
│   │   └── rag.py
│   └── tests/
│       ├── unit/
│       └── integration/
├── shared/
│   ├── config/
│   │   ├── backend.yaml
│   │   └── settings.py
│   ├── utils/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── security.py
│   ├── compliance/
│   │   ├── audit_utils.py
│   │   └── regulatory_checks.py
│   └── tests/
│       ├── unit/
│       └── integration/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/



## 2. Key Abstract Interfaces

*Do not change signatures without versioning.*

| **Purpose**           | **Interface**                          | **File**                                    |
|-----------------------|----------------------------------------|---------------------------------------------|
| API Endpoints         | `class APIEndpoints(ABC)`              | `backend/api/endpoints.py`                  |
| Data Models           | `class DataModels(ABC)`                | `backend/models/data_models.py`             |
| AI Services           | `class AIServices(ABC)`                | `ai_services/models/ai_models.py`           |
| Workflow Engine       | `class WorkflowEngine(ABC)`            | `backend/services/workflow_engine.py`       |
| Compliance Engine     | `class ComplianceEngine(ABC)`          | `backend/services/compliance.py`            |
| Metrics Emission      | `def emit_metric(name, **labels)`      | `shared/utils/metrics.py`                   |
| Audit Logging         | `def generate_audit_report(action)`     | `shared/compliance/audit_utils.py`          |
| Agent Interface (New) | `class AgentInterface(ABC)`            | `backend/agents/base_agent.py`              |

### AgentInterface (New)
```python
from abc import ABC, abstractmethod, abstractproperty

class AgentInput(BaseModel):
    """Base input schema for all agents."""
    project_id: str
    # Extend per agent

class AgentOutput(BaseModel):
    """Base output schema."""
    success: bool
    data: dict
    error: str = None

class AgentInterface(ABC):
    @abstractmethod
    def execute(self, input: AgentInput) -> AgentOutput:
        """Core execution method."""
        pass

    @property
    @abstractmethod
    def tools(self) -> list[dict]:
        """Declare tools (e.g., for OpenAI function-calling)."""
        return []  # e.g., [{"name": "web_search", "scopes": ["query:public"]}]
```
Deprecation Example

from deprecated import deprecated

class APIEndpoints(ABC):
    @deprecated("Use get_component_v2() instead")
    def get_component(self, id: str):
        pass

    def get_component_v2(self, id: str):
        # New method
        pass
## 3. Coding Conventions
Python 3.11: Use asyncio with async def and await for I/O operations. For LLM agents, use temperature=0 for determinism; ground prompts with RAG from KnowledgeBaseAgent.
TypeScript 5.3: Use strict type checking for frontend code.
Pydantic v2: For configuration and validation in Python.
Naming:
Python: snake_case for variables, PascalCase for classes, UPPER_SNAKE for constants.
JavaScript: camelCase for variables and functions, PascalCase for classes and components.
Type Hints: Mandatory in Python, enforced by pyright.
Logging:
Python: Use structlog via shared/utils/logging.py via shared/utils/logging.py; no print().
JavaScript: Use console.log with appropriate levels (info, warn, error).
Imports: Absolute from repo root (e.g., from backend.models.data_models import Component).
Error Handling: Use tenacity.retry for network calls in Python.
Compliance Tagging: Use @compliance_tag for auditable actions (e.g., component creation, workflow execution).


from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
def create_component(standard_code: str):
    return Component(standard_code=standard_code)
## 4. Extension Playbooks
### 4.1 Add a New Component

from backend.models.data_models import Component
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewComponent(Component):
    def __init__(self, standard_code: str):
        super().__init__(standard_code=standard_code)
        # Additional initialization for component-specific attributes
        self.description = "Custom component"
Add to shared/config/backend.yaml:


components:
  - standard_code: IEC-PV-300WXYZ-v1
    short_name: 300W Solar Panel
### 4.2 Add a New API Endpoint

from fastapi import APIRouter
from shared.compliance.regulatory_checks import compliance_tag

router = APIRouter()

@compliance_tag(regulation="IEC 81346")
@router.get("/new_endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
### 4.3 Add a New AI Model

from ai_services.models.ai_models import AIServices
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewAIModel(AIServices):
    def __init__(self):
        super().__init__()
        # Model-specific initialization
        self.model_path = "/path/to/new_model"
Register in shared/config/backend.yaml:


ai_services:
  models:
    - name: NewAIModel
      version: "1.0"
### 4.4 Add a New Workflow

from backend.services.workflow_engine import WorkflowEngine
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewWorkflow(WorkflowEngine):
    def __init__(self):
        super().__init__()
        # Workflow-specific initialization
        self.nodes = [{"id": "node1", "type": "custom_action"}]
Register in shared/config/backend.yaml:

workflows:
  - name: NewWorkflow
    version: 1
### 4.5 Add a New AI Agent (New)
Follow the Engineering Playbook (ENGINEERING_PLAYBOOK.md). Example:

from backend.agents.base_agent import AgentInterface
from langchain.tools import tool

class NewAgent(AgentInterface):
    @tool
    def custom_tool(self, params: dict):
        return {"result": "processed"}

    @property
    def tools(self):
        return [self.custom_tool]

    def execute(self, input: dict) -> dict:
        # LLM call with tools
        prompt = f"Process: {input['command']}. Use tools if needed."
        response = self.llm.call(prompt, tools=self.tools)  # OpenAI function-calling
        return {"output": response}
Register: register(NewAgent()) in backend/agents/init.py.

## 5. Environment Variables
Secrets are managed via HashiCorp Vault:

from shared.utils.security import get_secret

api_key = get_secret("API_KEY")
See .env.example for required variables:

API_KEY: API key for external services (e.g., Octopart).
DATABASE_URL: URL for PostgreSQL connection.
TEMPORAL_HOST: Host for self-hosted Temporal.io.
OPENAI_API_KEY: For LLM agents.
## 6. Testing & CI Guard-Rails
Pytest: Use for Python tests with pytest-asyncio and -n auto.
Jest: Use for JavaScript tests.
Property-Based Testing:

from hypothesis import given
from hypothesis.strategies import text
from backend.models.data_models import Component

@given(text(min_size=1))
def test_component_creation(standard_code):
    component = Component(standard_code=standard_code)
    assert component.standard_code == standard_code
LLM Output Validation:

@pytest.mark.llm
def test_response_schema():
    response = {"standard_code": "IEC-PV-300WXYZ-v1", "data": {}}
    assert validate_llm_output(response, JSON_SCHEMA)
For agents, test LLM outputs with mock responses; use LangChain evaluators for hallucinations. Example:

from langchain.evaluation import load_evaluator

def test_agent_output():
    evaluator = load_evaluator("qa")
    score = evaluator.evaluate({"input": test_input, "prediction": agent.execute(test_input)})
    assert score > 0.9
CI Checks: Fail PRs if:
Coverage <90%.
Lint errors (flake8, pyright for Python; ESLint for JavaScript).
Docs build fails (MkDocs).
Synthetic .cgraph validation fails.
## 7. Code Generation Hints
Import from interfaces to reduce coupling (e.g., backend.models.data_models.Component).
Include docstrings for all functions and classes for Docusaurus auto-docs.
Use sentinel comments (# <codex-marker>) for idempotent edits.
Generate alembic migrations for persistence changes.
Wrap network calls in tenacity.retry for Python.
Use @compliance_tag for auditable actions.
For agents, generate Spec Cards first (from ENGINEERING_PLAYBOOK.md); use events for dependencies.
## 8. Common Tasks Cheat-Sheet
Run backend
poetry run uvicorn backend.main:app --reload

Run frontend
npm run start

Run tests
pytest -q
npm test

Lint and type-check
pre-commit run --all-files

Generate docs
mkdocs serve

Run agent tests: pytest backend/agents/
## 9. Danger Zones & Recommended Practices

PitfallWhy It HurtsRecommended Practice
Circular ImportsRuntime crashesImport from interfaces (e.g., backend.models.data_models).
Blocking CPUSpikes latencyUse asyncio.to_thread() in Python.
Unlogged ActionsCompliance violationsLog via structlog via shared/utils/logging.py.
Inconsistent SchemasData integrity issuesValidate against retention_policy in DataModels.
LLM HallucinationsInaccurate designsUse RAG grounding and temperature=0; add bias checks if bias_guard: true.
## 10. Common Recipes
### 10.1 Add a New Component

from backend.models.data_models import Component
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewComponent(Component):
    def __init__(self, standard_code: str):
        super().__init__(standard_code=standard_code)
        # Additional initialization
        self.description = "Custom component"
### 10.2 Emit a Metric

hared.utils.metrics import emit_metric

emit_metric("component_creation", standard_code="IEC-PV-300WXYZ-v1", value=1)
### 10.3 Test LLM Output

@pytest.mark.llm
def test_response_schema():
    response = {"standard_code": "IEC-PV-300WXYZ-v1", "data": {}}
    assert validate_llm_output(response, JSON_SCHEMA)
### 10.4 Add a New Workflow

from backend.services.workflow_engine import WorkflowEngine
from shared.compliance.regulatory_checks import compliance_tag

@compliance_tag(regulation="IEC 81346")
class NewWorkflow(WorkflowEngine):
    def __init__(self):
        super().__init__()
        # Workflow-specific initialization
        self.nodes = [{"id": "node1", "type": "custom_action"}]
### 10.5 Integrate LLM in Agent

from backend.agents.base_agent import AgentInterface
from langchain.tools import tool

class NewAgent(AgentInterface):
    @tool
    def custom_tool(self, params: dict):
        return {"result": "processed"}

    @property
    def tools(self):
        return [self.custom_tool]

    def execute(self, input: dict) -> dict:
        # LLM call with tools
        prompt = f"Process: {input['command']}. Use tools if needed."
        response = self.llm.call(prompt, tools=self.tools)  # OpenAI function-calling
        return {"output": response}
## 11. Repository Manifest

OriginFlow/
├── .env.example
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── Dockerfile
├── requirements.txt
├── scripts/
│   ├── deploy.sh
│   ├── test.sh
│   ├── lint.sh
├── docs/
│   ├── api/
│   ├── guides/
│   │   ├── setup.md
│   │   ├── new_component.md
│   │   ├── new_workflow.md
│   │   └── troubleshooting.md
│   └── prd/
│       └── OriginFlow_PRD_v1.4.1.md
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── cd.yml
│   └── dependabot.yml
├── frontend/
│   ├── components/
│   │   ├── EngineeringCanvas.tsx
│   │   ├── ProjectWizard.tsx
│   │   ├── ComponentPackStudio.tsx
│   │   ├── AdminConsole.tsx
│   │   └── WorkflowDiffViewer.tsx
│   ├── pages/
│   │   ├── Home.tsx
│   │   └── Dashboard.tsx
│   ├── utils/
│   │   ├── state.ts
│   │   └── telemetry.ts
│   └── tests/
│       ├── unit/
│       └── integration/
├── backend/
│   ├── api/
│   │   ├── endpoints.py
│   │   ├── compliance.py
│   │   ├── workflows.py
│   │   ├── media.py
│   │   └── model_registry.py
│   ├── services/
│   │   ├── workflow_engine.py
│   │   ├── compliance.py
│   │   ├── datasheet_processor.py
│   │   ├── naming_engine.py
│   │   └── audit.py
│   ├── models/
│   │   ├── data_models.py
│   │   └── migrations/
│   ├── agents/  # New: For AI agents
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── registry.py
│   │   ├── orchestrator.py
│   │   ├── system_design_agent.py
│   │   └── tests/
│   └── tests/
│       ├── unit/
│       └── integration/
├── ai_services/
│   ├── models/
│   │   ├── vision.py
│   │   ├── nlp.py
│   │   └── model_registry.py
│   ├── utils/
│   │   ├── validation.py
│   │   └── rag.py
│   └── tests/
│       ├── unit/
│       └── integration/
├── shared/
│   ├── config/
│   │   ├── backend.yaml
│   │   └── settings.py
│   ├── utils/
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   └── security.py
│   ├── compliance/
│   │   ├── audit_utils.py
│   │   └── regulatory_checks.py
│   ├── errors/  # New: For AgentError enum
│   │   └── agent_errors.py
│   └── tests/
│       ├── unit/
│       └── integration/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
## 12. Decision-Making Framework
Event-Driven Architecture: Use Kafka for scalability; avoid direct calls.
Data Models: Use immutable dataclasses (e.g., Component, Workflow) with retention_policy.
Dependencies: Use stdlib and OSS (e.g., pandas); heavy libraries as optional extras.
New Packages: Create under shared/ or ai_services/ if imported by >2 domains or >500 LOC.
Agent Orchestration: Use BusinessOrchestratorAgent for routing; prefer event-sourcing for async.
## 13. Safe-Guards for Autonomous Agents
Run pytest and npm test after code generation; abort on failure.
Seek human approval for interface changes.
Mask secrets in logs with ***.
Use @compliance_tag for auditable actions (e.g., component creation, workflow execution).
Wrap network calls in tenacity.retry for Python.
Validate Spec Cards in CI; run bias audits for ethical agents.
## 14. Agent Taxonomy Overview
See AGENT_TAXONOMY.md for full list. Agents are modular, with Spec Cards defining I/O.

## 15. References
Engineering Playbook: ENGINEERING_PLAYBOOK.md
Contribution Guidelines: CONTRIBUTING.md
