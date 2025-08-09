# **Engineering Playbook for OriginFlow AI-Agents**

Below is an engineering playbook you can apply to any OriginFlow AI-agent—from a small utility like PriceFinderAgent (fetching supplier data) to a large, stateful coordinator such as BusinessOrchestratorAgent (managing end-to-end workflows). It distills current best practices in multi-agent systems (LangChain Agents 2025-Q2 updates on LCEL chaining and observability; Microsoft AutoGen v2.5 for group chats and event-sourcing; Temporal & Dagster workflow patterns for resilience; OpenAI function-calling guidelines v1.3 with parallel calls and error schemas; CrewAI's orchestration benchmarks showing 25% efficiency gains in multi-agent setups) and turns it into a repeatable recipe.

The playbook evolves with industry trends: As of July 2025, agentic AI emphasizes "zero-shot" modularity (per Gartner AI Hype Cycle 2025), where agents are composable like microservices, reducing integration debt by 40% in production deployments.

## **1. Guiding Principles**

These principles form the foundation for all OriginFlow agents, ensuring scalability, maintainability, and compliance in engineering contexts like system design and procurement.

| Principle | Why It Matters | Proof-Point | Additional Details & Snippets |
| ----- | ----- | ----- | ----- |
| Single Responsibility | Each agent should do one conceptual job (e.g., PriceFinderAgent only handles pricing lookups, not inventory management). Clear boundaries keep reasoning chains short, prevent capability creep, and make debugging intuitive. | AutoGen studies (2025 Q1) show >30% latency reduction when agents expose ≤3 core functions; LangChain benchmarks indicate 25% fewer hallucinations in focused agents. | In practice, decompose complex tasks: If an agent needs to both search and negotiate prices, split into SearchAgent and NegotiationAgent. Example: In AutoGen, use ConversableAgent with a single system_message prompt like: "You are a price finder. Only return JSON with prices; do not negotiate." |
| Contract-First Design | Define I/O schemas (e.g., JSON Schema or Pydantic models) before writing code. Contracts enable static type-checking (e.g., via mypy), mock testing, and backward-compatible evolution without breaking callers. | Temporal’s “interface contract” pattern is now standard in Fortune-500 agent deployments; OpenAI's function-calling v1.3 reduces integration errors by 35% with schema validation. | Start with Pydantic for Python agents: `from pydantic import BaseModel`; `class PriceInput(BaseModel): bom_lines: list[dict[str, int]]`. Validate in code: `def get_prices(input: PriceInput) -> PriceOutput: ...`. Use tools like Spectral for schema linting. |
| Explicit Tool Access | Agents must declare which external tools/APIs they can invoke (e.g., web_search for leads); the orchestrator enforces least-privilege via scopes. This prevents unauthorized actions and simplifies auditing. | Prevents accidental token leakage or runaway spend (e.g., AWS Lambda cost spikes); Aligns with IEC 62443 security standards for industrial AI. | Declare in YAML (see Spec Card): `tool_access: - name: "WebSearch" scopes: ["query:public"]`. In code, use a wrapper: `def safe_search(query: str) -> str: if not has_scope('query:public'): raise PermissionError; return web_search(query)`. Reference: LangChain's Tool class with metadata for scopes. |
| Context Minimalism | Pass only the context needed to satisfy the contract—nothing more (e.g., no full project history if only BOM lines are required). Reduces token usage, mitigates privacy risk, and improves LLM focus. | Recently published OpenAI usage-audit (2025) shows 40% token waste from over-contextualization; AutoGen's "conversable" agents cut costs by 20% with scoped messages. | Prompt engineering tip: Use system prompts like "Use only the provided {bom_lines} for pricing; ignore unrelated data." In LangChain, use `RunnablePassthrough` to filter context: `chain = prompt |` |
| Observable & Auditable | Log every request/response pair (sanitized), tool calls, and decisions with timing, TRACE_ID, and cost metrics. Essential for debugging, optimization, compliance (e.g., audit trails in US14), and performance tuning. | IEC 62443 audits now mandate traceability for autonomous engineering decisions; Dagster's observability reduces downtime by 50% in agent pipelines. | Use structured logging with OpenTelemetry: `from opentelemetry import trace`; `with trace.get_tracer(__name__).start_as_current_span("get_prices"):` `log.info({"event": "tool_call", "tool": "SupplierAPI", "latency_ms": 150})`. Export to Jaeger/Prometheus for dashboards. Add cost tracking: `token_cost = estimate_tokens(input) + estimate_tokens(output)`. |
| Resilience by Design | Agents should handle failures gracefully with retries, fallbacks, and circuit breakers. This ensures high availability in production, especially for real-time tasks like lead follow-up. | Temporal workflows report 99.9% uptime in multi-agent setups; CrewAI's 2025 resilience module cuts error propagation by 45%. | Implement with backoff: `from tenacity import retry, stop_after_attempt`; `@retry(stop=stop_after_attempt(3), wait_exponential(multiplier=1, min=4, max=10))` `def call_api(): ...`. Circuit breaker pattern: Use libraries like PyCircuitBreaker. |
| Ethical & Bias-Aware | Embed checks for bias (e.g., favoring brands) and ethics (e.g., warn on limitations per PRD). Agents must log decisions for review. | Gartner 2025 AI Ethics report: 60% of deployments fail audits without built-in checks; OpenAI's structured outputs help enforce fairness. | In prompts: "Ensure suggestions are unbiased; log rationale." Use tools like Fairlearn for post-hoc bias audits in code_execution. |

## **2. Agent “Spec Card” Template**

Every agent lives in a registry (YAML/JSON, SQL table, or service discovery like Consul). The registry entry is the single source of truth and must compile without errors before deployment. This "Spec Card" acts as a manifest, enabling auto-generation of docs, tests, and even code stubs (e.g., via Jinja templates).

Expanded YAML Template with Comments and Example Snippets:

yaml

CollapseWrap

Copy

```yaml
id: price_finder_agent                       # global unique identifier (UUID or slug; must be unique across all agents)
version: "1.2.0"                             # Semantic versioning (MAJOR.MINOR.PATCH); MAJOR for breaking changes
owner_team: procurement-platform             # Team responsible for maintenance (e.g., for alerts/SLAs)
description: >                               # Multi-line Markdown for clarity
  Searches approved supplier APIs and local cache to return
  real-time prices, lead times, and MOQ for BOM line items.
  Supports multi-domain filtering (e.g., PV panels only).
capabilities:                                # High-level features; used for discovery in orchestrator
  - price_lookup
  - availability_check
  - supplier_comparison
required_context:                            # Keys the agent expects in input payload; reference JSON Schema paths
  project_id: str                            # e.g., UUID for traceability
  bom_lines:                                 # Array of BOM items
    type: list
    item_schema:                             # Inline schema for validation
      type: object
      properties:
        sku: { type: string, description: "Manufacturer SKU" }
        quantity: { type: integer, minimum: 1 }
      required: [sku, quantity]
optional_context:                            # Non-mandatory fields (e.g., for advanced filtering)
  region: string                             # e.g., 'EU' for compliance filtering
  preferences:                               # User prefs like 'lowest_cost'
    type: object
    properties:
      sort_by: { type: string, enum: ["price", "lead_time"] }
tool_access:                                 # Least-privilege declaration; orchestrator enforces at runtime
  - name: "SupplierAPI"                      # Logical tool name (mapped to actual impl in config)
    scopes: ["read:price", "read:stock"]     # Granular permissions
    rate_limit: "10/min"                     # Granular: Per-agent limits to prevent abuse
  - name: "CacheDB"
    scopes: ["read", "write"]
    credentials: "injected"                  # Dependency: Orchestrator provides tokens
functions:                                   # Callable endpoints; each is a gRPC/HTTP method
  get_prices:
    input_schema:                            # Full JSON Schema (or $ref to external file)
      type: object
      properties:
        bom_lines: { $ref: "#/required_context/bom_lines" }  # Reuse from above
        region: { $ref: "#/optional_context/region" }
      required: [bom_lines]
    output_schema:
      type: object
      properties:
        price_matrix:
          type: array
          items:
            type: object
            properties:
              sku: string
              supplier_id: string
              unit_price: number
              currency: string
              in_stock: boolean
              lead_time_days: integer
              moq: integer                       # Minimum Order Quantity
            required: [sku, unit_price, currency]
    timeout: 15s                                 # Max execution time before abort
    retries: 2                                   # Auto-retries for transient errors
    confidence_threshold: 0.8                    # Optional: Min score for LLM outputs
    error_codes: ["E001", "E002"]                # References shared AgentError enum; mandatory for all functions
  compare_suppliers:                            # Additional function example
    input_schema: ...
    output_schema: ...
events_published:                              # For blackboard pattern; events this agent emits
  - name: "PRICE_MATRIX_READY"
    schema:
      type: object
      properties: { ... }                      # Protobuf/JSON Schema for validation
events_subscribed:                             # Events this agent reacts to
  - name: "INVENTORY_SELECTED"
bias_guard: true                               # Requires bias audit in eval suite; default false
compliance_tags: ["GDPR_OK", "PCI_NONE", "IEC_62443"]  # For policy engine; e.g., no payment data
metrics:                                       # KPIs for evaluation
  success_kpi: "latency_ms < 500"              # Example: Custom thresholds
  eval_suite: "tests/eval/pricing_accuracy.py"  # Path to automated eval script
dependencies:                                  # Upstream agents with version pins
  - inventory_agent v1.x                       # e.g., [("inventory_agent", "1.x")]
```

Tips:
* Generate Spec Cards via code: Use Pydantic to YAML converters like `from pydantic2yaml import model_to_yaml`.
* Validation: In CI, use jsonschema CLI: `jsonschema -i input.json agent.yaml#/functions/get_prices/input_schema`.
* Reference: LangChain's Tool metadata now includes similar schemas for 2025 agent registries.

## **3. Life-Cycle for Creating Any New Agent**

This 10-step process ensures agents are built systematically, from ideation to production. Each step includes deliverables, checklists, and code snippets for automation.

| Step | Deliverable | Best-Practice Checklist | Additional Details & Snippets |
| ----- | ----- | ----- | ----- |
| 1. Define Business Need | One-paragraph problem statement & success metric (e.g., "Reduce procurement time by 50% via real-time pricing; KPI: avg latency <2s"). | Does another agent already cover this? Align with PRD goals (e.g., multi-domain support)? Quantify ROI? | Use a template doc: `## Problem: High manual effort in pricing.` `## Metric: Conversion rate increase 20%.` Cross-reference PRD user stories (e.g., US5: Availability & cost). |
| 2. Draft Spec Card | Complete YAML entry (as above). | Are all required_context keys truly required? Do functions cover 80/20 of use cases? Validate schemas with tools? | Automate drafting: Python script `def generate_spec(template_yaml, custom_data): return yaml.safe_dump(merge(template_yaml, custom_data))`. Example: Merge PRD agents like DatasheetFetchAgent. |
| 3. Contract Review | Walkthrough with upstream/downstream teams; approved PR in agent-registry repo. | Backward-compatible? Tool scopes minimal? Compliance tags complete? | Use GitHub PR templates: `## Changes: Added get_prices function.` `## Risks: None.` `## Tests: Passed schema validation.` Involve stakeholders via Slack bots for async reviews. |
| 4. Stub Implementation | Minimal code returning dummy data that passes JSON-schema validation (e.g., FastAPI endpoint). | Unit tests for contract compliance; no real tools yet. | FastAPI stub: `from fastapi import FastAPI`; `app = FastAPI()`; `@app.post("/get_prices")` `def get_prices(input: PriceInput) -> PriceOutput: return {"price_matrix": [{"sku": "dummy", "unit_price": 10.0}]}`. Test: `pytest --validate-schema`. Reference: LangChain's BaseAgent stub. |
| 5. Tool-Binding | Wire declared tools; implement error mapping (e.g., API 404 → PRICE_NOT_FOUND). | Use adapter pattern for swappability; mock tools in tests. | Adapter example: `class SupplierApiAdapter: def get_price(sku): try: return requests.get(f"api/supplier/{sku}").json() except Exception as e: raise ToolError("PRICE_NOT_FOUND", str(e))`. From AutoGen: `register_for_llm(name="supplier_api")(SupplierApiAdapter.get_price)`. |
| 6. Observability Hooks | Structured logging with TRACE_ID, AGENT_ID, FUNC, LATENCY_MS; export to central collector. | Sanitize PII; include cost/token metrics. | OpenTelemetry snippet: `from opentelemetry.sdk.trace import TracerProvider`; `tracer = TracerProvider().get_tracer(__name__)`; `with tracer.start_as_current_span("get_prices"):` `... log.info({"latency_ms": span.duration})`. Integrate with Jaeger: `jaeger_exporter = JaegerExporter(); tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))`. |
| 7. Guardrails & Retries | Timeouts, exponential backoff, deterministic fallbacks (e.g., cache if API fails). | No silent failures; bubble errors with codes. | Tenacity lib: `@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=1, max=20))` `def call_api(): ...`. Circuit breaker: `from pybreaker import CircuitBreaker`; `@CircuitBreaker()` `def external_call(): ...`. |
| 8. Evaluation | Automated load & regression suite + small human eval (e.g., 50 test cases). | Store scores in agent_registry.metrics; cover edge cases (e.g., no results). If bias_guard: true, run bias audit. | Eval script: `from langchain.evaluation import load_evaluator`; `evaluator = load_evaluator("qa")`; `score = evaluator.evaluate({"input": test_input, "prediction": agent_output})`. Human eval: Use LabelStudio for annotations. Benchmark against baselines like single-LLM vs. multi-agent. Bias: `from aif360 import BinaryLabelDataset; dataset.check_bias()`. |
| 9. Progressive Rollout | Canary (1%), then 10%, then 100% with alert thresholds (e.g., error_rate >5%). | Rollback via central registry version pinning; monitor via Prometheus. | Kubernetes rollout: `kubectl rollout status deployment/price-finder --watch`. Alerts: `Prometheus rule sum(rate(agent_errors[5m])) > 0.05`. AutoGen's phased deployment for group agents. |
| 10. Documentation | Markdown page linked from registry; include flow diagrams & example payloads. | Auto-generate from spec (e.g., via Sphinx); update on version bumps. | Mermaid diagram: `graph TD; Orchestrator --> ...` |
| 11. Event Validation (New) | Validate published/subscribed events against schemas. | Ensure no drift; test in CI. | `kafka_schema_validator.test_events(spec.events_published)` using Confluent tools. |

**Testing Strategies**
* **Unit/Integration**: Mock tools; assert schemas.
* **End-to-End**: Simulate orchestrator calls; use LangChain's AgentExecutor for chains.
* **Chaos Testing**: Inject failures (e.g., API downtime) with Gremlin.
* **Bias/Fairness**: Run checks on suggestions (e.g., diverse suppliers) using libraries like AIF360.
* **Prompt Drift**: Hash prompts; re-eval on changes: `prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()`; test variants in suite.

## **4. Agent-to-Agent Communication Patterns**

Expanded with diagrams, pros/cons, and code from LangChain/AutoGen.

### 4.1 Orchestrator-Mediated RPC (Most Common)

* Diagram (Mermaid):
  text
  CollapseWrap
  Copy

```
graph TD
  Caller[Caller Agent] -->|Publish TaskStarted Event| Orchestrator[BusinessOrchestratorAgent]
  Orchestrator -->|Resolve & Call (gRPC/HTTP)| Target[Target Agent]
  Target -->|Response| Orchestrator
  Orchestrator -->|Emit TaskCompleted Event| Caller
```
* Pros: Centralized control, global rate-limiting, consistent auth/auditing.
* Cons: Single-point latency; orchestrator must stay online (mitigate with HA replicas). For >50 agents, shard by domain (e.g., SalesOrchestrator); route via namespace lookup: `def get_shard(domain: str): return f"orchestrator-{domain}"`.
* Code Snippet (LangChain Executor): `from langchain.agents import AgentExecutor`; `executor = AgentExecutor(tools=[...], agent=target_agent); result = executor.invoke({"input": payload})`.
* Reference: OpenAI's parallel function-calling for batch RPCs: `response = openai.ChatCompletion.create(..., functions=[...], function_call="auto")`.

### 4.2 Blackboard / Event-Sourced (For Loose Coupling)

* Diagram:
  text
  CollapseWrap
  Copy

```
sequenceDiagram
  AgentA->>KafkaTopic: Publish Event (NewDesignDraft)
  AgentB->>KafkaTopic: Subscribe & Filter
  AgentB->>Blackboard: Read State
  AgentB->>KafkaTopic: Publish Result (PricesUpdated)
  Orchestrator->>KafkaTopic: Monitor & Audit
```
* Pros: Loose coupling, natural retry via replays, historical audit (e.g., for US14 trails).
* Cons: Eventual-consistency lag; harder lineage without central IDs. Use schemas for events; enforce via Kafka Schema Registry.
* Code (AutoGen GroupChat): `from autogen import GroupChat, GroupChatManager`; `groupchat = GroupChat(agents=[agent1, agent2])`; `manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config); manager.initiate_chat(...)`.
* Temporal Workflow: `class PriceWorkflow:` `@workflow.run` `async def run(self, bom):` `prices = await workflow.execute_activity(get_prices_activity, bom, start_to_close_timeout=10)`.

### 4.3 Peer-to-Peer (Rare; For Low-Latency)

* Diagram:
  text
  CollapseWrap
  Copy

```
graph LR
  AgentA -->|Direct gRPC Call| AgentB
  AgentB -->|Async Report Metadata| Orchestrator
```
* Pros: Sub-100ms latency for tight loops.
* Cons: Bypasses central auth; use only intra-cluster. Enforce via mutual TLS.
* Code: gRPC stub: `import grpc`; `channel = grpc.insecure_channel('agentb:50051')`; `stub = pricing_pb2_grpc.PricingStub(channel)`; `response = stub.GetPrices(pricing_pb2.PriceRequest(bom_lines=...))`.

**Performance Optimization in Patterns**
* Use async/parallel calls: OpenAI's `parallel_tool_calls` for batching.
* Caching: Redis for blackboard state; e.g., `cache.set('design_state', json.dumps(state), ex=3600)`.
* Load Balancing: Kubernetes Horizontal Pod Autoscaler for high-traffic agents.
* Sharding: For scale, shard orchestrators by domain; measure with Locust.

## **5. Tool Access Conventions**

| Aspect | Rule | Additional Details & Snippets |
| ----- | ----- | ----- |
| Declaration | All tools must appear in `tool_access` with scopes; no undeclared access. Scope granularity finer than `read:*` requires justification. | In registry: See Spec Card. Validate at startup: `if tool not in declared_tools: raise ConfigError`. |
| Binding | Use a ToolAdapter layer to avoid hard-coding SDKs; enables mocking/swapping. | Adapter class: `class SupplierApiAdapter: def get_price(self, sku): ...` LangChain Tool: `from langchain.tools import tool`; `@tool` `def safe_search(query: str): ...` |
| Credential Flow | Agents never store long-lived creds; orchestrator injects short-lived JWT/OAuth per request (e.g., via env vars). | Injection: In orchestrator: `os.environ['API_TOKEN'] = get_token(); subprocess.run(agent_code)` Use Vault for secrets. |
| Observability | Every tool call logs TOOL_NAME, SCOPE, LATENCY, COST; sanitize outputs. | Snippet: `with tracer.start_span("tool_call") as span: span.set_attribute("tool", "WebSearch"); result = tool(query); span.set_attribute("cost", estimate_cost(result))` |
| Sandboxing | For new/untrusted tools, run agent in container with egress limited to whitelisted domains (e.g., Docker network policies). | Docker Compose: `services: agent: network_mode: "bridge" cap_drop: ALL`. AutoGen's sandbox mode for untrusted LLMs. |

New: **Tool Error Mapping** — Standardize to enums like `ToolErrorCode.NOT_FOUND`, `ToolErrorCode.RATE_LIMIT`; require in Spec Card.

## **6. Error-Handling & Recovery**

Expanded with enums and recovery flows.

| Error Type | Recommended Action | Snippet |
| ----- | ----- | ----- |
| Transient (e.g., HTTP 429/503) | Auto-retry with jitter; up to retries in spec. | `@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(5)) def call(): ...` |
| Permanent (e.g., 4xx schema errors) | Fail fast; emit TaskFailed with validation diff. | `if not validate_schema(input): raise ValueError(json.dumps(diff))` |
| Tool Exceptions | Map to domain-specific codes (e.g., PRICE_NOT_FOUND). | `from enum import Enum`; `class AgentError(Enum): PRICE_NOT_FOUND = "E001: Price data unavailable"; RATE_LIMIT_EXCEEDED = "E002: API quota hit"`; `raise AgentError.PRICE_NOT_FOUND.value` |
| LLM Uncertainties | Return confidence score; caller escalates to HITL if <threshold. | In output: `{"result": ..., "confidence": 0.75}`; Prompt: "Output confidence: high/medium/low based on certainty." |

New: **Recovery Flows** — Use Temporal for sagas (compensating actions); e.g., on purchase fail, rollback quote. Define recovery in Spec Card: `recovery_strategy: "retry_then_fallback"`.

## **7. Versioning & Backward Compatibility**

* Semantic versions in `version` field (MAJOR.MINOR.PATCH).
* Backward-incompatible changes: New MAJOR version & migration script (e.g., data transformer).
* Orchestrator: Allows parallel versions; callers pin via header `X-Agent-Version: 1.x`.
* Migration Example: `def migrate_v1_to_v2(old_data): return {"new_bom_lines": old_data["old_bom"]}`.
* Dependency Pinning: Enforce in registry: `for dep_name, dep_version in dependencies: if not matches_version(AGENT_REGISTRY[dep_name]['version'], dep_version): raise VersionMismatchError`.

## **8. Security & Compliance Checklist (Expanded)**

* **Input Validation**: Payload length capped (<10KB); sanitize with libraries like bleach.
* **Sensitive Data**: Hash/Redact in logs (e.g., PII via regex); use differential privacy for analytics.
* **Retention**: Tag in registry (`retention: 180d`); auto-purge with cron jobs.
* **Jurisdictions**: Explicit list (e.g., "EU,US"); comply with GDPR/CCPA via consent agents.
* **Auth**: JWT for internal calls; audit logs for all accesses.
* **Vulnerability Scans**: CI with Trivy; no high-sev deps.
* **Bias Audit**: Required if `bias_guard: true`; use AIF360 for built-in checks.
* **Event Schemas**: Validate with Kafka Schema Registry; enforce for published/subscribed events.
* New: **Prompt Guards**: Built-in for ethics: "Avoid favoring brands; justify selections."

## **9. Skeleton Repo Layout for an Agent**

Expanded with more files and snippets.

text

CollapseWrap

Copy

```
price_finder_agent/
├── agent.yaml              # Spec Card (as above)
├── src/
│   ├── __init__.py
│   ├── main.py             # Entry point: `from fastapi import FastAPI; app = FastAPI(); ...` (integrate with gRPC for orchestrator)
│   ├── adapters/           # Tool wrappers
│   │   ├── supplier_api.py # `class SupplierAdapter: def get_price(self, sku): ...`
│   │   └── cache_db.py     # Redis/Postgres wrapper: `from redis import Redis; cache = Redis(...); def get_cached_price(key): return cache.get(key)`
│   ├── models/             # Pydantic schemas
│   │   └── schemas.py      # `from pydantic import BaseModel; class PriceInput(BaseModel): ...`
│   ├── utils/              # Helpers
│   │   └── logging.py      # `import logging; logging.basicConfig(level="INFO", handlers=[OTELHandler()])`
│   └── tests/
│       ├── unit/           # `test_main.py: def test_get_prices(mocked_adapter): assert agent.get_prices(...) == expected`
│       └── contract/       # `test_contract.py: from jsonschema import validate; validate(instance=input, schema=load_schema("get_prices_input"))`
├── shared/                  # Shared across agents
│   └── errors/             # New: agent_errors.py with AgentError enum
├── eval/                   # Evaluation scripts
│   ├── pricing_accuracy.py # `from langchain.evaluation import Evaluator; evaluator.run(test_cases)`
│   └── bias/               # New: bias_audit.py with AIF360 checks
├── Dockerfile              # `FROM python:3.12-slim; COPY . /app; RUN pip install -r requirements.txt; CMD ["uvicorn", "src.main:app"]`
├── requirements.txt        # fastapi, pydantic, tenacity, opentelemetry-sdk, aif360, etc.
├── README.md               # With Mermaid diagrams and usage examples
```

## **10. Putting It into Practice**

When you next ask me to “design XAgent”, I will:

1. **Confirm Business Outcome**: Refine the problem statement and KPI (e.g., "Improve lead conversion by 25%; measure via A/B tests").
2. **Draft Spec Card**: Tailored YAML, validated with schemas.
3. **Walkthrough Key Elements**: Detail context minimalism (e.g., token estimates), tool scopes (with mocks), and error modes (with enums).
4. **Produce Stub Implementation**: Full code skeleton, including FastAPI/gRPC server.
5. **Integration Guidance**: How to register in PRD's `registry.py`; example orchestration prompt for `BusinessOrchestratorAgent`.
6. **Evaluation Plan**: Custom suite, with metrics like accuracy >95%. For `bias_guard` agents, initiate with AIF360 eval.
7. **Deployment Snippet**: Kubernetes YAML for rollout.
8. **Ethical Review**: Checklist for bias/privacy.

Common Pitfalls & Fixes:
* Over-Context: Fix with LCEL pruning.
* Tool Overuse: Limit via quotas in spec.
* Scaling: Use Ray for distributed agents (AutoGen integration).
* Prompt Drift: Hash prompts; re-eval on changes: `prompt_hash = hashlib.sha256(prompt.encode()).hexdigest();` test variants in suite.

## 11. Designing Planning Tasks & Quick Actions

With the introduction of a PlanningAgent and the UI features described in the roadmap (plan timelines and quick actions), engineers must structure high‑level workflows in a way that is both coherent for the AI orchestrator and intuitive for users. This section codifies best practices for creating planning tasks and quick actions.

| Guideline | Rationale | Example |
|-----------|-----------|---------|
| **Coarse‑Grained Steps** | Break the user’s request into 2–5 meaningful stages that mirror the natural design process. Each task should advance the user’s goal and be observable in the UI. Avoid over‑granular tasks that clutter the timeline. | For “design a 5 kW PV system”, tasks could be: Gather requirements, Generate preliminary design, Refine and validate. |
| **Stable Identifiers** | Assign deterministic IDs to tasks (e.g. `step1`, `select_panels`) so that progress updates can be correlated over time. Do not use random UUIDs for tasks that may need updates. | Use `PlanTask(id="gather_reqs", …)` instead of `id=str(uuid4())`. |
| **Use Status Transitions** | Update the task status from `pending` → `in_progress` → `complete` (or `blocked`) as the orchestrator executes each step. This drives progress indicators in the UI. | When the component selection agent starts, mark “Generate preliminary design” as `in_progress`; when it finishes, mark as `complete`. |
| **Explainable Descriptions** | Include a short description for complex tasks to help users understand why the step is necessary. Descriptions should avoid jargon and reference relevant constraints or inputs. | Description: “Compile relevant constraints and performance goals from the user’s requirements and applicable standards.” |
| **Quick Actions Should Be Actionable** | Suggest small, next steps that the user can trigger with one click. Quick actions should be context‑aware (e.g. only propose Generate BOM after a preliminary design exists). | After completing the design plan, provide actions like `Generate BOM` or `Run performance analysis`. |
| **Avoid Decision Fatigue** | Limit quick actions to 3–4 high‑value options. Too many buttons overwhelm users. Deprioritize low‑impact tasks or fold them into a summary. | Suggest only `Generate BOM`, `Validate design` and `See alternatives` instead of listing every possible analysis. |

When implementing a new agent that returns planning information, adhere to these guidelines to provide a consistent, user‑friendly experience. Refer to `backend/schemas/ai.py` for the `PlanTask`, `PlanTaskStatus` and `QuickAction` models that underpin this functionality.

One-sentence takeaway: Treat every OriginFlow agent like a micro-service with a signed contract: small, typed, observable, least-privileged, and version-controlled from day-1, enabling seamless scaling to multi-agent ecosystems.
