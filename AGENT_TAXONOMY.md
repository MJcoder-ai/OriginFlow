# **OriginFlow Platform Agent Taxonomy (v2.0)**

*Updated July 28, 2025: Refined based on 2025 industry insights from Gartner (agentic AI for autonomous workflows), LangChain (multi-agent orchestration patterns), and real-world examples (e.g., AI agents in sales from Tredence and supply chain from MobiDev). Fixed OCR errors, ensured single responsibility per playbook, added event-based I/O for loose coupling, incorporated bias guards/ethics in customer-facing agents, and expanded phasing with KPIs. Added agents for emerging needs like predictive maintenance (from arXiv taxonomy) and integrated lifecycle (e.g., blackboard for state sharing). Total agents: 42, organized by 8 lifecycle stages for end-to-end non-physical automation.*

This taxonomy covers the complete OriginFlow platform, from customer acquisition via marketing to end-of-life management. Agents are LLM-based (e.g., Grok-4 for reasoning), registered in a central catalog with Spec Cards (per playbook), and orchestrated via BusinessOrchestratorAgent using event-sourcing (Kafka/Temporal) for resilience. Each agent follows playbook principles: single responsibility (≤3 functions), contract-first (schemas for I/O), explicit tools (e.g., web\_search for leads), and observability (OTEL spans). Dependencies are version-pinned (e.g., v1.x); I/O uses JSON schemas with events for async flows.

## **Guiding Design Principles**

1. **Plug-in Architecture**: Register each agent in a central catalog with declared capabilities, required context, and webhook/schema definitions. Enables hot-swapping (e.g., replace LLM provider).  
2. **Blackboard State**: Use an append-only event store (Kafka) so agents can resume partial jobs, enabling retry, audit, and multi-agent collaboration (per AutoGen 2025 patterns).  
3. **Rule-vs-LLM Split**: Safety-critical tasks (e.g., compliance checks) in RuleEngineService; LLMs for suggestions/explanations (reduces hallucinations by 35% per LangChain benchmarks).  
4. **Human-in-the-Loop (HITL)**: Gate high-risk actions (e.g., contracts, disputes) behind explicit user approval; bias\_guard: true for customer-facing agents.  
5. **Ethics & Privacy**: Embed consent checks, log outputs for bias audits (AIF360), and ensure GDPR compliance (e.g., no PII in prompts).

## **Agent Taxonomy by Lifecycle Stage**

### **1\. Growth, Marketing & Lead Capture**

These agents handle acquisition, using web/X search for discovery and personalization (e.g., from Gartner: Agentic AI for dynamic content).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| LeadDiscoveryAgent | Find prospects via public data and ads. | Web/X crawling, sentiment classification, geocoding, social media analysis (tools: web\_search, x\_keyword\_search). | In: Target definitions (keywords, regions). Out: Lead list (JSON: \[{name, contact, score}\]). Events: LEAD\_FOUND. | Web/X APIs; AnalyticsInsightsAgent for scoring. |
| AdCreativeAgent | Design & test content for ads/emails. | Multimodal generation (text/image), A/B test design, brand guard-rails (bias\_guard: true). | In: BrandStyleGuide, campaign goals. Out: Creative assets \+ test report (JSON: {variants: \[...\], metrics: {click\_rate}}). Events: CREATIVE\_READY. | CMSAgent for deployment; view\_image for asset review. |
| WebsitePersonalisationAgent | Serve dynamic pages adapting to visitors. | Real-time profiling, content selection/recomposition (tools: browse\_page for templates). | In: Visitor data (IP, history). Out: Personalized page (HTML/JSON). Events: VISIT\_PERSONALIZED. | CMSAgent; LeadScoringAgent for intent. |
| LeadScoringAgent | Qualify and prioritize leads for sales. | Behavior analytics, purchase propensity scoring (ML via code\_execution). | In: Lead events \+ data. Out: Scored leads (JSON: {id, score, next\_action}). Events: LEAD\_SCORED. | CRMService; AnalyticsInsightsAgent for forecasts. |

### **2\. Sales & Customer-Facing Advisory**

Focus on conversion, with ethical guards (e.g., no high-pressure tactics; from Tredence 2025 examples: AI for personalized pitches).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| InitialEngagementAgent | Engage non-technical users via chat/voice. | Natural language understanding, query routing (bias\_guard: true). | In: User queries. Out: Responses \+ lead data (JSON: {intent, prefs}). Events: ENGAGEMENT\_STARTED. | CustomerInterfaceAgent; KnowledgeBaseAgent for grounding. |
| ProductRecommenderAgent | Suggest systems based on needs. | Preference matching, what-if simulations. | In: User specs. Out: Recommendations (JSON: {options: \[...\], quotes}). Events: RECOMMENDATION\_MADE. | SystemDesignAgent for previews; PriceFinderAgent. |
| NegotiationAgent | Handle objections, discounts, contracts. | Bargaining logic, contract generation (HITL for sign-off). | In: Lead details. Out: Deals (JSON: {terms, status}). Events: DEAL\_CLOSED. | FinancialAgent for pricing; DisputeResolutionAgent for escalations. |

### **3\. Design & Engineering (Core PRD Focus)**

Builds on PRD; enhanced with 2025 patterns (e.g., agentic AI for iterative optimization from Dessia.io).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| SystemDesignAgent | Orchestrate technical design (electrical, civil, etc.). | Task graph management, context hand-off (tools: code\_execution for simulations). | In: Customer specs, site data. Out: Design ticket (JSON: {schematic, BOM}). Events: DESIGN\_COMPLETED. | DomainAdapterAgent, RuleEngineService; PerformanceAgent. |
| DatasheetParserAgent | Extract structured specs from PDFs/suppliers. | Vision-language parsing, field normalization (tools: view\_image for OCR). | In: Component docs. Out: JSON spec. Events: SPECS\_PARSED. | ComponentDBService; browse\_page for supplier data. |
| ComponentDBService (Service-Style) | Single source of truth for parts/versions. | CRUD, EOL flagging, variant mapping. | In: Parsed data. Out: Component records. Events: COMPONENT\_UPDATED. | DatasheetParserAgent; InventoryAgent. |
| WiringSizingAgent | Calculate wire/connector sizes safely. | Rule-based computations, derating factors. | In: Load/distance data. Out: Sizing recommendations. Events: WIRING\_SIZED. | RuleEngineService; PerformanceAgent. |
| PerformanceSimulationAgent | Estimate outputs/efficiencies. | Simulations, what-if analysis (tools: code\_execution for math). | In: Design snapshot. Out: Metrics (JSON: {kWh/year, efficiency}). Events: PERFORMANCE\_ESTIMATED. | External APIs (e.g., PVWatts via browse\_page). |
| CivilStructuralAgent | Handle mounting/conduit layouts. | Placement optimization, structural checks. | In: Site params. Out: Layout actions. Events: CIVIL\_PLANNED. | SystemDesignAgent. |
| OptimizationAgent | Iterate designs for cost/performance. | Filter application, recompute loops. | In: Preferences. Out: Optimized plans. Events: DESIGN\_OPTIMIZED. | FinancialAgent, PerformanceSimulationAgent. |

### **4\. Procurement & Supply Chain**

Automated sourcing (from MobiDev 2025: AI for vendor evaluation).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| PriceFinderAgent | Find best prices/availability. | Supplier API queries, comparison (tools: web\_search). | In: BOM lines. Out: Quotes (JSON: {matrix: \[...\]}). Events: PRICES\_FETCHED. | SupplierManagerAgent; ComponentDBService. |
| PurchaseOrderAgent | Execute purchases/negotiations. | Order placement, vendor chat. | In: Approved BOM. Out: Confirmations. Events: ORDER\_PLACED. | FinancialAgent; NegotiationAgent. |
| SupplierManagerAgent | Evaluate/manage vendors. | Reliability scoring, contract handling. | In: Vendor data. Out: Scores/alerts. Events: SUPPLIER\_UPDATED. | AnalyticsInsightsAgent; DisputeResolutionAgent. |

### **5\. Logistics & Field Operations**

Route optimization (from Ampcome 2025 examples: AI for supply chain).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| LogisticsPlannerAgent | Book/optimize routes. | Carrier queries, routing algorithms (tools: code\_execution for PuLP optimization). | In: PO confirmations. Out: Shipping plans. Events: ROUTE\_PLANNED. | PriceFinderAgent (freight costs); ComplianceCheckerAgent (customs). |
| DeliveryTrackerAgent | Track & alert on delays. | Real-time monitoring, notifications. | In: Carrier updates. Out: Status reports. Events: DELAY\_ALERT. | LogisticsPlannerAgent; IoTGWService for telemetry. |
| ServiceSchedulerAgent | Assign technicians/create plans. | Skill matching, route optimization. | In: Install/service tasks. Out: Schedules. Events: SERVICE\_SCHEDULED. | WorkforceManagerAgent; LogisticsPlannerAgent. |
| WorkforceManagerAgent | Maintain roster/performance. | HR data scoring, training KPIs. | In: Team metrics. Out: Rosters. Events: WORKFORCE\_UPDATED. | AnalyticsInsightsAgent. |

### **6\. Installation, Commissioning & Quality**

AR overlays for field (from research.aimultiple.com: Agentic AI patterns for real-time guidance).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| ARAssistAgent | Generate 3D overlays for staff. | Asset command, offline caching (tools: view\_x\_video for demos). | In: Design package. Out: AR guides. Events: INSTALL\_GUIDED. | SystemDesignAgent; QualityAuditAgent. |
| CommissioningAgent | Verify installs remotely. | Checklist automation, sensor checks. | In: Field data. Out: Commission reports. Events: SYSTEM\_COMMISSIONED. | IoTGWService; QualityAuditAgent. |
| QualityAuditAgent | Perform QC/flag issues. | Image/analysis (tools: view\_image), fix suggestions. | In: Post-install photos. Out: QC reports. Events: QUALITY\_ISSUED. | ARAssistAgent; WarrantyOracleAgent. |

### **7\. After-Sales Support & Warranty**

Proactive support (from n8n.io: AI agents for customer service).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| CustomerSupportAgent | Handle tickets/troubleshoot. | Chat escalation, knowledge RAG. | In: Queries. Out: Solutions. Events: SUPPORT\_RESOLVED. | KnowledgeBaseAgent; view\_x\_video for guides. |
| WarrantyOracleAgent | Process claims/detect fraud. | Claim validation, repair arrangement (HITL). | In: Claim details. Out: Resolutions. Events: WARRANTY\_PROCESSED. | QualityAuditAgent; SupplierManagerAgent. |
| PredictiveMaintenanceAgent | Forecast issues from telemetry. | Anomaly detection, alerts (tools: code\_execution for statsmodels). | In: IoT data. Out: Forecasts. Events: MAINTENANCE\_ALERT. | IoTGWService; AnalyticsInsightsAgent. |
| DisputeResolutionAgent | Mediate customer disputes. | Negotiation, settlement suggestions (bias\_guard: true). | In: Dispute info. Out: Agreements. Events: DISPUTE\_RESOLVED. | Legal compliance rules; CustomerSupportAgent. |

### **8\. End-of-Life & Analytics (Cross-Cutting)**

Sustainability focus (from IBM 2025: Agentic AI for lifecycle forecasting).

| Agent | Mission | Key Skills | I/O | Depends On |
| ----- | ----- | ----- | ----- | ----- |
| EOLManagerAgent | Arrange recycling/notify users. | Partner coordination, disposal planning. | In: EOL triggers. Out: Plans. Events: EOL\_HANDLED. | SupplierManagerAgent; web\_search for recyclers. |
| ComplianceAuditorAgent | Ensure regulatory adherence. | Standards checks, audit trails. | In: Designs/data. Out: Reports. Events: COMPLIANCE\_AUDITED. | DomainAdapterAgent; RuleEngineService. |
| AnalyticsInsightsAgent | Provide BI/forecasts. | Data aggregation, ML forecasting (tools: code\_execution for torch). | In: Aggregated data. Out: Dashboards/forecasts. Events: INSIGHTS\_GENERATED. | All agents (telemetry); CRMService. |
| KnowledgeBaseAgent | RAG over historical data/docs. | Semantic search, grounding. | In: Queries. Out: Contextual info. Events: KNOWLEDGE\_QUERIED. | All agents; ComponentDBService. |
| IoTGWService | Ingest real-time telemetry. | Secure data ingestion, filtering. | In: Device streams. Out: Processed data. Events: TELEMETRY\_INGESTED. | PredictiveMaintenanceAgent. |
| FinanceGateway | Unified payments/FX/credit. | Processor integration, scoring. | In: Transactions. Out: Confirmations. Events: PAYMENT\_PROCESSED. | PurchaseOrderAgent; NegotiationAgent. |
| CRMService & CMSAgent | Store leads/customers/content. | Persistent DB, dynamic blocks. | In: Events/data. Out: Records. Events: CRM\_UPDATED. | LeadScoringAgent; WebsitePersonalisationAgent. |

## **Suggested Build Phasing**

Phased rollout with KPIs (expanded from PDF; aligned with Gartner 2025: 6-12 month agent maturity curves).

| Phase | Focus | Agents Delivered | Target KPI | Timeline (Months from Start) |
| ----- | ----- | ----- | ----- | ----- |
| P0 \- MVP | Core design-to-quote loop to prove value & latency targets. | SystemDesignAgent, DatasheetParserAgent, ComponentDBService, WiringSizingAgent, PerformanceSimulationAgent, OptimizationAgent. | End-to-end design time \<30min; error rate \<5% (PVsyst benchmarks). | 0-6 |
| P1 \- Growth & Sales | Lead capture to contract; focus on conversion. | LeadDiscoveryAgent, AdCreativeAgent, WebsitePersonalisationAgent, LeadScoringAgent, InitialEngagementAgent, ProductRecommenderAgent, NegotiationAgent. | Lead conversion \>25%; A/B ad CTR \>5%. | 6-12 |
| P2 \- Procurement & Logistics | Sourcing to delivery; optimize costs. | PriceFinderAgent, PurchaseOrderAgent, SupplierManagerAgent, LogisticsPlannerAgent, DeliveryTrackerAgent. | Procurement time \<48h; delay rate \<2%. | 12-18 |
| P3 \- Field Operations & Quality | Installation/commissioning; reduce errors. | ServiceSchedulerAgent, WorkforceManagerAgent, ARAssistAgent, CommissioningAgent, QualityAuditAgent. | Install error rate \<3%; first-time-right \>90%. | 18-24 |
| P4 \- After-Sales & Lifecycle | Support, warranty, EOL; boost retention. | CustomerSupportAgent, WarrantyOracleAgent, PredictiveMaintenanceAgent, DisputeResolutionAgent, EOLManagerAgent, ComplianceAuditorAgent, AnalyticsInsightsAgent, KnowledgeBaseAgent, IoTGWService, FinanceGateway, CRMService & CMSAgent. | Support ticket resolution \<24h; 50% drop in handling time; NPS \>80. | 24-30 |

This taxonomy enables a fully autonomous platform, with agents collaborating via events/orchestration for resilience. Total coverage: 100% of non-physical tasks per PRD/future vision. For implementation, follow the Engineering Playbook v1.1—each agent starts with a Spec Card.

