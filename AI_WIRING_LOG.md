# AI Wiring Log and Compliance Overview

The AI wiring pipeline now produces a structured pipeline log that captures progress messages, stage transitions, and compliance issues. This information can be surfaced in a dedicated front-end tab or panel, giving designers real-time insight into what the system is doing and highlighting any problems that need attention.

## How the log works

Each run of the wiring pipeline creates a `PipelineLog` object (defined in `backend/schemas/pipeline.py`). The log includes the `session_id`, a chronological list of `PipelineLogEntry` items, and an optional list of `compliance_issues`.

A `PipelineLogEntry` captures the timestamp, the pipeline stage (such as `panel_grouping`, `suggestion_generation`, or `topology_generation`), a human-readable message, and a log level (`info`, `warning`, `error`, `compliance`, or `debug`).

Compliance issues are extracted during validation with enhanced categorization:

- **String Sizing Issues**: Violations of minimum/maximum string length requirements
- **Electrical Code Issues**: NEC/IEC code compliance violations  
- **Voltage/Current Limits**: Exceeding safe operating limits
- **Grounding Requirements**: Missing or improper grounding connections
- **Protection Device Requirements**: Missing overcurrent or surge protection

The AI wiring API endpoint attaches this log to the response under the `log` key, so the front-end can present it alongside the updated graph or patch.

## Enhanced Enterprise Features

### Pipeline Stages

The enhanced pipeline includes comprehensive stage tracking:

1. **Initialization** - Session setup and component analysis
2. **Component Analysis** - Detailed component inventory and validation
3. **Panel Grouping** - Intelligent panel string formation with compliance checking
4. **Pattern Retrieval** - Vector store search for similar historical designs
5. **Suggestion Generation** - AI-powered wiring recommendation generation
6. **Topology Generation** - Enterprise electrical topology creation
7. **Compliance Validation** - Comprehensive code compliance checking
8. **Enterprise Validation** - Additional enterprise policy validation
9. **Optimization** - Performance and efficiency optimization
10. **Finalization** - Result preparation and audit trail completion

### Compliance Categories

The system now tracks detailed compliance issues across multiple categories:

- **ELECTRICAL_CODE**: NEC/IEC code violations with specific references
- **STRING_SIZING**: String length and module count compliance
- **VOLTAGE_LIMITS**: Operating voltage validation
- **CURRENT_LIMITS**: Current capacity and ampacity checking
- **GROUNDING**: Equipment and system grounding requirements
- **PROTECTION**: Overcurrent protection and surge protection devices
- **CONDUIT_FILL**: Conduit fill calculations and NEC compliance
- **ACCESSIBILITY**: Code accessibility and maintenance requirements

Each compliance issue includes:
- Detailed message and code reference (e.g., "NEC 690.7(A)")
- Affected component IDs for precise issue location
- Suggested remediation steps
- Risk level assessment (low/medium/high/critical)
- Approval requirement flag for enterprise workflows

## Front-end integration

### AI Wiring Log Tab

Create a new tab (e.g., "AI Wiring Log") that appears in the same table where "Single-Line Diagram" is located, positioned after the "ODL Code" tab. This tab should be shown after the user invokes the AI wiring task.

### API Integration

#### Enhanced Endpoint

Use the new enhanced endpoint for comprehensive logging:

```http
POST /api/v1/ai/wiring/enhanced
Content-Type: application/json

{
  "session_id": "session_123",
  "max_modules_per_string": 12,
  "min_modules_per_string": 2,
  "use_llm": false,
  "enable_logging": true
}
```

#### Response Structure

The enhanced response includes comprehensive logging data:

```json
{
  "success": true,
  "message": "Generated 8 AI-optimized connections",
  "edges_added": 8,
  "warnings": [],
  "performance_metrics": {
    "total_duration_ms": 2341,
    "stages_completed": 7,
    "compliance_checks": 3
  },
  "session_version": 15,
  "log": {
    "pipeline_info": {
      "id": "pipeline_20250825_143210",
      "session_id": "session_123", 
      "started_at": "2025-08-25T14:32:10.123Z",
      "completed_at": "2025-08-25T14:32:12.464Z",
      "status": "completed"
    },
    "timeline": [
      {
        "timestamp": "2025-08-25T14:32:10.125Z",
        "stage": "initialization",
        "level": "info",
        "message": "Starting AI wiring pipeline",
        "duration_ms": null,
        "components": []
      },
      {
        "timestamp": "2025-08-25T14:32:10.234Z",
        "stage": "panel_grouping", 
        "level": "info",
        "message": "Formed 3 panel groups",
        "duration_ms": 89,
        "components": ["panel_1", "panel_2", "panel_3"]
      },
      {
        "timestamp": "2025-08-25T14:32:11.456Z",
        "stage": "compliance_validation",
        "level": "compliance",
        "message": "[STRING_SIZING] String 2 has only 1 module (minimum 2 required)",
        "duration_ms": null,
        "components": ["panel_2"]
      }
    ],
    "compliance_issues": [
      {
        "type": "string_sizing",
        "severity": "compliance",
        "message": "String 2 has only 1 module (minimum 2 required)",
        "code_reference": "NEC 690.7(A) - String sizing requirements",
        "components_affected": ["panel_2"],
        "remediation": "Adjust panel grouping to meet minimum string size or update inverter specifications",
        "risk_level": "medium",
        "requires_approval": false
      }
    ],
    "summary": {
      "total_stages": 7,
      "total_entries": 23,
      "compliance_issues": 1,
      "critical_issues": 0,
      "warnings": 2,
      "errors": 0
    },
    "configuration": {
      "max_modules_per_string": 12,
      "min_modules_per_string": 2,
      "use_llm": false,
      "compliance_checks_enabled": true
    },
    "exportable": true
  },
  "compliance_summary": {
    "total_issues": 1,
    "critical_issues": 0,
    "string_sizing_issues": 1,
    "electrical_code_issues": 0,
    "requires_approval": false
  },
  "export_available": true
}
```

### UI Implementation Guidelines

#### Timeline Display

Display entries in reverse chronological order with their timestamps, stages and messages. Use different colors or icons to distinguish info, warning, error, and compliance levels:

- **Info**: Blue icon, normal text
- **Warning**: Yellow/orange icon, emphasized text
- **Error**: Red icon, bold text  
- **Compliance**: Purple/orange icon with code reference
- **Debug**: Gray icon, muted text (hidden by default)

#### Compliance Issues Section

Surface compliance issues at the top of the tab (or in a prominent alert) so that designers can address them immediately. For each issue show:

- Issue type and severity level
- Detailed message with code reference
- Affected components (with click-to-highlight functionality)
- Suggested remediation steps
- Risk level indicator

#### Performance Metrics

Display key performance metrics in a summary panel:

- Total execution time
- Stages completed successfully
- Components processed
- Connections generated
- Compliance checks performed

#### Export Functionality

Provide a download option to export the log and compliance report for audit purposes. Support multiple formats:

- **JSON**: Full structured data for programmatic analysis
- **CSV**: Timeline entries for spreadsheet analysis
- **PDF**: Formatted compliance report for documentation
- **TXT**: Human-readable log for troubleshooting

This is particularly useful for enterprise customers who need traceability and approval workflows.

## Example Log Display

An example log might look like:

| Time (UTC) | Stage | Level | Message |
|------------|--------|--------|---------|
| 2025-08-25 14:32:12 | finalization | info | Pipeline completed successfully: 8 connections, 1 compliance issue |
| 2025-08-25 14:32:11 | topology_generation | info | Created 8 validated connections |
| 2025-08-25 14:32:11 | compliance_validation | compliance | [STRING_SIZING] String 2 has only 1 module (minimum 2 required) |
| 2025-08-25 14:32:11 | suggestion_generation | info | Generated 6 wiring suggestions |
| 2025-08-25 14:32:10 | pattern_retrieval | info | Retrieved 2 similar designs |
| 2025-08-25 14:32:10 | panel_grouping | info | Formed 3 panel groups |
| 2025-08-25 14:32:10 | component_analysis | info | Analyzed 8 components: {'panel': 6, 'inverter': 1, 'meter': 1} |
| 2025-08-25 14:32:10 | initialization | info | Starting AI wiring pipeline |

In this case, the designer would know that one string is under-sized and can adjust the layout or grouping parameters accordingly.

## Integration with Existing Architecture

### Formal ODL Schema Compliance

The enhanced logging system maintains full compatibility with the formal ODL schema:

- Uses `source_id/target_id` naming conventions for edge references
- Stores metadata in formal `attrs` dictionaries
- Integrates with `ODLGraph` versioning and session management
- Supports optimistic concurrency control with proper version tracking

### Enterprise Features Integration

The logging system integrates with existing enterprise features:

- **Vector Store**: Logs pattern retrieval results and similarity scores
- **Compliance Engine**: Detailed compliance validation with code references  
- **Audit Trails**: Comprehensive audit logging for enterprise governance
- **Risk Management**: Risk level assessment and approval workflow integration
- **Performance Monitoring**: Detailed performance metrics and optimization tracking

### Tool Architecture Compatibility

Maintains compatibility with the platform's tool architecture:

- Returns proper `ODLPatch` operations for orchestrator integration
- Supports typed `AIWiringInput` parameters with validation
- Integrates with existing API endpoints and request/response patterns
- Provides backward compatibility for legacy pipeline calls

This comprehensive logging system elevates the AI wiring experience to enterprise-grade standards while maintaining the platform's architectural integrity and performance characteristics.