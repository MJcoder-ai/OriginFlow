# 🤖 AI Agents Developer Guide for OriginFlow

*This guide provides comprehensive documentation for developing, deploying, and scaling AI agents in the OriginFlow platform. It covers both the current Phase 1 implementation and the roadmap to enterprise-level multi-agent systems.*

> **Golden Rule:** *Never* break public contracts. Create a v2 interface and mark v1 as deprecated if changes are needed.

## 🚀 **Current Status: Phase 1 Agent Architecture**

OriginFlow implements a **modular AI agent system** for engineering design automation:
- ✅ **18 Core Agents** implemented with basic intelligence
- ✅ **Confidence-Driven Autonomy** with learning loop  
- ✅ **Vector Store Integration** (Qdrant/Chroma)
- ✅ **Simple Registry-Based Orchestration**
- ⏳ **Enterprise Vision**: 42-agent ecosystem with event-driven workflows

---

## 1. Current Project Structure (Phase 1)

OriginFlow uses a **simplified architecture** optimized for core engineering design functionality:
OriginFlow/
├── backend/
│   ├── agents/                    # 🤖 AI Agents (18 implemented)
│   │   ├── __init__.py           # Agent auto-registration
│   │   ├── base.py               # AgentBase interface  
│   │   ├── registry.py           # Simple agent registry
│   │   ├── learning_agent.py     # Confidence scoring & autonomy
│   │   ├── system_design_agent.py # High-level design orchestration
│   │   ├── wiring_agent.py       # Wire sizing with rule engine
│   │   ├── performance_agent.py   # Performance estimation
│   │   ├── financial_agent.py    # Cost calculations
│   │   └── [+13 more agents]     # See AGENT_TAXONOMY.md
│   ├── api/routes/               # API endpoints
│   │   ├── ai.py                # /ai/command endpoint
│   │   ├── analyze.py           # /ai/analyze-design
│   │   ├── feedback_v2.py       # Learning feedback logging
│   │   └── [+7 more routes]
│   ├── services/                # Core services
│   │   ├── ai_service.py        # AiOrchestrator with auto-approval
│   │   ├── vector_store.py      # Qdrant/Chroma integration
│   │   ├── embedding_service.py # SentenceTransformer + OpenAI
│   │   ├── rule_engine.py       # Deterministic calculations
│   │   └── [+10 more services]
│   ├── models/                  # SQLAlchemy models
│   │   ├── ai_action_log.py     # Feedback logging  
│   │   ├── ai_action_vector.py  # Vector embeddings
│   │   ├── component.py         # Component entities
│   │   └── [+4 more models]
├── frontend/                    # React TypeScript app
│   ├── src/components/          # UI components
│   │   ├── ChatPanel.tsx        # AI chat interface
│   │   ├── ChecklistPanel.tsx   # Action approval UI
│   │   ├── Workspace.tsx        # Design canvas
│   │   └── [+25 more components]
│   ├── src/services/
│   │   ├── api.ts              # Backend API client
│   │   └── types.ts            # TypeScript interfaces
├── docs/
│   ├── AGENT_TAXONOMY.md       # 42-agent enterprise roadmap
│   ├── ENGINEERING_PLAYBOOK.md # Agent development guide
│   ├── feedback_logging.md     # Learning system docs
│   └── troubleshooting.md
└── qdrant_storage/             # Vector database (optional)



## 2. Core Agent Interface (Phase 1)

*Current implementation uses simplified interfaces. Enterprise interfaces planned for Phase 2.*

### AgentBase (Current Implementation)
```python
# backend/agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class AgentBase(ABC):
    """Common interface for all agents."""
    
    name: str = ""           # Agent identifier for registry
    description: str = ""    # Human-readable description
    
    @abstractmethod
    async def handle(self, command: str) -> List[Dict[str, Any]]:
        """Process command and return list of action dictionaries."""
        raise NotImplementedError
```

### Agent Registry (Current Implementation)  
```python
# backend/agents/registry.py
from backend.agents.base import AgentBase

_agents: Dict[str, AgentBase] = {}

def register(agent: AgentBase) -> AgentBase:
    """Register agent with @register decorator."""
    _agents[agent.name] = agent
    return agent

def get_agent(name: str) -> AgentBase:
    """Retrieve registered agent by name.""" 
    return _agents[name]
```

### Key Service Interfaces

| **Service**           | **Interface**                    | **File**                          |
|-----------------------|----------------------------------|-----------------------------------|
| Agent Base            | `class AgentBase(ABC)`           | `backend/agents/base.py`         |
| AI Orchestrator       | `class AiOrchestrator`           | `backend/services/ai_service.py` |
| Vector Store          | `class VectorStore(Protocol)`    | `backend/services/vector_store.py` |
| Embedding Service     | `class EmbeddingService`         | `backend/services/embedding_service.py` |
| Learning Agent        | `class LearningAgent`            | `backend/agents/learning_agent.py` |
---

## 3. Agent Development Guide (Phase 1)

### 3.1 Quick Start - Creating a New Agent
```python
# 1. Create agent file: backend/agents/my_agent.py
from backend.agents.base import AgentBase
from backend.agents.registry import register
from backend.schemas.ai import AiActionType

@register
class MyAgent(AgentBase):
    name = "my_agent"
    description = "Does something useful"
    
    async def handle(self, command: str) -> List[Dict[str, Any]]:
        # Parse command (currently: regex/string matching)
        if "hello" in command.lower():
            return [{
                "action": AiActionType.validation,
                "payload": {"message": "Hello from MyAgent!"},
                "version": 1
            }]
        return []

# 2. Import in backend/agents/__init__.py  
from . import my_agent  # noqa: F401

# 3. Test via API:
# POST /api/v1/ai/command {"command": "hello world"}
```

### 3.2 Current Development Patterns

**Command Parsing (Phase 1):**
```python
# Pattern matching with regex
import re
text = command.lower()
kw_match = re.search(r"(\d+(?:\.\d+)?)\s*(kw|kilowatt)", text)
if kw_match:
    size_kw = float(kw_match.group(1))
```

**Action Creation:**
```python
return [{
    "action": AiActionType.add_component,  # Use enum values
    "payload": {
        "type": "panel",
        "name": "Solar Panel",
        "x": 100, "y": 100
    },
    "version": 1
}]
```

**Learning Integration:**
- Actions automatically get confidence scores from `LearningAgent`
- High-confidence actions (>0.8) are auto-approved
- All decisions logged to `ai_action_log` table


## 4. Implemented Agents (Phase 1 - 18 Total)

### 4.1 Core Design Agents
- **SystemDesignAgent**: High-level design orchestration with component suggestions
- **WiringAgent**: Wire sizing using deterministic rule engine (fully implemented)
- **PerformanceAgent**: Basic performance estimation with heuristic formulas
- **FinancialAgent**: Cost estimation using per-kW pricing heuristics

### 4.2 Component & Data Management
- **ComponentAgent**: Component CRUD operations
- **InventoryAgent**: Component library management
- **BomAgent**: Bill of materials generation
- **DatasheetFetchAgent**: PDF parsing and extraction

### 4.3 Support & Validation Agents
- **LearningAgent**: Confidence scoring and auto-approval decisions
- **CrossLayerValidationAgent**: Design validation (basic checks)
- **AuditorAgent**: Design auditing and compliance
- **SourcingAgent**: Component sourcing and alternatives

### 4.4 Layout & Connection Agents  
- **LinkAgent**: Connection management between components
- **LayoutAgent**: Component positioning and layout optimization
- **DesignAssemblyAgent**: Sub-assembly generation

### 4.5 Knowledge & Routing
- **KnowledgeManagementAgent**: Knowledge queries and retrieval
- **RouterAgent**: Command routing to appropriate agents

---

## 5. Enterprise Roadmap (Phases 2-4)

**Current Status**: 18/42 agents implemented (43%)  
**Enterprise Goal**: Full lifecycle automation with 42 specialized agents

### 5.1 Phase 2: Business Automation (6-12 months)
**Target**: Sales & procurement workflow automation

**Missing Agents (7 planned):**
- **LeadDiscoveryAgent**: Find prospects via web/social search
- **AdCreativeAgent**: Generate marketing content with A/B testing
- **ProductRecommenderAgent**: AI-powered system recommendations  
- **PriceFinderAgent**: Multi-supplier price comparison
- **PurchaseOrderAgent**: Automated procurement workflows
- **SupplierManagerAgent**: Vendor evaluation and management
- **NegotiationAgent**: Contract negotiation assistance

**Technical Upgrades:**
- Event-driven architecture with Temporal.io workflows
- Advanced tool access control and security
- Multi-agent collaboration patterns
- External API integrations (CRM, ERP, supplier APIs)

### 5.2 Phase 3: Field Operations (12-18 months)  
**Target**: Installation, commissioning & quality automation

**Missing Agents (10 planned):**
- **LogisticsPlannerAgent**: Route optimization and scheduling
- **ServiceSchedulerAgent**: Technician assignment and planning
- **ARAssistAgent**: Augmented reality installation guidance
- **CommissioningAgent**: Remote system verification
- **QualityAuditAgent**: Automated quality control with image analysis
- **WorkforceManagerAgent**: Team performance and training
- **DeliveryTrackerAgent**: Real-time logistics monitoring

**Technical Upgrades:**
- IoT device integration and telemetry processing
- Computer vision for quality inspection
- Mobile/AR application integration
- Real-time collaboration tools

### 5.3 Phase 4: Lifecycle Management (18-24 months)
**Target**: Support, warranty & end-of-life automation  

**Missing Agents (7 planned):**
- **CustomerSupportAgent**: Intelligent ticket resolution
- **WarrantyOracleAgent**: Automated warranty processing
- **PredictiveMaintenanceAgent**: Failure prediction from telemetry
- **DisputeResolutionAgent**: Conflict mediation and resolution
- **EOLManagerAgent**: End-of-life and recycling coordination
- **ComplianceAuditorAgent**: Regulatory compliance automation
- **AnalyticsInsightsAgent**: Business intelligence and forecasting

**Technical Upgrades:**
- Advanced predictive analytics with ML models
- Compliance automation and audit trails
- Customer self-service portals
- Sustainability and ESG reporting

---

## 6. Configuration & Environment (Phase 1)

### 6.1 Required Environment Variables
```bash
# .env file configuration
OPENAI_API_KEY=sk-...                    # Required: OpenAI API for LLM calls
DATABASE_URL=sqlite:///./originflow.db   # Optional: Defaults to SQLite
```

### 6.2 Optional Vector Store Configuration  
```bash
# Qdrant (default vector store)
VECTOR_BACKEND=qdrant                    # qdrant (default) or chroma
QDRANT_HOST=localhost                    # Default: localhost
QDRANT_COLLECTION=ai_action_vectors      # Default collection name
VECTOR_SIZE=384                          # Embedding dimensions

# Chroma (alternative vector store)  
CHROMA_COLLECTION=ai_action_vectors      # Collection name
CHROMA_PERSIST_DIR=/data/chroma          # Persistence directory
```

### 6.3 Agent Configuration
```python
# backend/config.py - Agent settings
openai_model_router: str = "gpt-4o-mini"     # Router agent model
openai_model_agents: str = "gpt-4o-mini"     # Agent LLM model  
temperature: float = 0.0                     # Deterministic responses
max_tokens: int = 512                        # Response length limit
embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
```

### 6.4 Future Configuration (Phase 2+)
```bash
# Planned for enterprise phases
TEMPORAL_HOST=localhost:7233             # Workflow orchestration
KAFKA_BROKERS=localhost:9092             # Event streaming
VAULT_ADDR=https://vault.company.com     # Secrets management
GRAFANA_URL=https://grafana.company.com  # Observability
```
---

## 7. Testing & Quality Assurance

### 7.1 Agent Testing (Current)
```python
# backend/agents/test_my_agent.py
import pytest
from backend.agents.my_agent import MyAgent

@pytest.mark.asyncio
async def test_agent_basic_functionality():
    agent = MyAgent()
    result = await agent.handle("hello world")
    
    assert len(result) == 1
    assert result[0]["action"] == "validation"
    assert "Hello" in result[0]["payload"]["message"]

# Test with confidence scoring
def test_agent_confidence_integration():
    # Test that agent actions get proper confidence scores
    # from the learning system
    pass
```

### 7.2 Integration Testing
```python
# Test full AI command flow
@pytest.mark.asyncio 
async def test_ai_command_endpoint():
    response = await client.post("/api/v1/ai/command", 
                               json={"command": "design 5kW solar system"})
    assert response.status_code == 200
    actions = response.json()
    assert len(actions) > 0
    assert all("confidence" in action for action in actions)
```

### 7.3 Learning System Testing
```python
# Test confidence scoring and auto-approval
def test_learning_loop():
    # 1. Submit action for approval
    # 2. Approve action (creates training data)  
    # 3. Submit same action again
    # 4. Verify higher confidence and potential auto-approval
    pass
```

---

## 8. Migration Path to Enterprise

### 8.1 Phase 1 → Phase 2 Migration
1. **Event System**: Replace direct calls with event-driven patterns
2. **Advanced Orchestration**: Implement Temporal.io workflows  
3. **Tool Security**: Add scope-based tool access control
4. **External APIs**: Integrate with CRM, ERP, supplier systems

### 8.2 Development Best Practices
- **Start Simple**: Use Phase 1 patterns for new agents
- **Plan for Scale**: Design with enterprise patterns in mind
- **Test Thoroughly**: Include confidence scoring in all tests
- **Document Everything**: Maintain agent spec cards (ENGINEERING_PLAYBOOK.md)

### 8.3 Enterprise Readiness Checklist
- [ ] Event-driven architecture implementation
- [ ] Multi-agent collaboration patterns  
- [ ] Advanced security and compliance
- [ ] Performance monitoring and optimization
- [ ] Regulatory audit trail capabilities

---

*For detailed agent development guidelines, see [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md)*  
*For complete agent taxonomy and roadmap, see [AGENT_TAXONOMY.md](AGENT_TAXONOMY.md)*
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
