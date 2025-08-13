# Placeholder Components System

## Overview

The Placeholder Components System in OriginFlow allows users to start designing solar systems even when specific component datasheets are not available. The system uses generic placeholder components with reasonable default values to enable rapid prototyping and iterative design refinement.

## Architecture

### Core Components

1. **PlaceholderComponentService** (`backend/services/placeholder_components.py`)
   - Manages placeholder component definitions
   - Validates placeholder attributes
   - Creates placeholder nodes for ODL graphs
   - Provides component sizing estimates

2. **ComponentSelectorAgent** (`backend/agents/component_selector_agent.py`)
   - Finds real components to replace placeholders
   - Ranks candidates by suitability
   - Manages bulk replacement operations

3. **Enhanced ODL Schemas** (`backend/schemas/odl.py`)
   - Extended with placeholder support
   - New component candidate definitions
   - Requirements management structures

## Placeholder Component Types

### Generic Panel (`generic_panel`)
- **Default Power**: 400W
- **Default Voltage**: 24V
- **Default Efficiency**: 20%
- **Default Area**: 2.0 m²
- **Replacement Categories**: panel, pv_module, solar_panel

### Generic Inverter (`generic_inverter`)
- **Default Capacity**: 5000W
- **Default Efficiency**: 95%
- **Input Voltage Range**: 200-600V
- **Output Voltage**: 240V
- **Replacement Categories**: inverter, string_inverter, power_optimizer, microinverter

### Generic Mount (`generic_mount`)
- **Load Rating**: 50 kg
- **Tilt Angle**: 30°
- **Material**: Aluminum
- **Wind Rating**: 150 km/h
- **Replacement Categories**: mounting, rail, clamp, roof_mount

### Generic Cable (`generic_cable`)
- **Gauge**: 10AWG
- **Voltage Rating**: 600V
- **Ampacity**: 30A
- **Default Length**: 10m
- **Replacement Categories**: cable, wire, dc_cable, pv_wire

### Generic Fuse (`generic_fuse`)
- **Rating**: 15A
- **Voltage Rating**: 600V
- **Type**: DC
- **Interrupting Capacity**: 10,000A
- **Replacement Categories**: fuse, breaker, disconnect, combiner

### Generic Battery (`generic_battery`)
- **Capacity**: 10 kWh
- **Voltage**: 48V
- **Chemistry**: LiFePO4
- **Cycle Life**: 6000 cycles
- **Round Trip Efficiency**: 95%
- **Replacement Categories**: battery, energy_storage, battery_pack

### Generic Monitoring (`generic_monitoring`)
- **Communication**: WiFi
- **Power Consumption**: 5W
- **Data Logging**: Enabled
- **Web Interface**: Available
- **Replacement Categories**: monitoring, gateway, data_logger

## Usage Workflow

### 1. Design Generation with Placeholders

When real components are not available, the PVDesignAgent automatically generates placeholder components:

```python
# Example: Generate placeholder design
design_result = await pv_agent.execute(session_id, "generate_design")
```

This creates a complete system design using generic components that can be immediately visualized and analyzed.

### 2. Component Selection Process

Once real components become available (through datasheet uploads), users can replace placeholders:

```python
# Find candidates for placeholders
candidates = await component_selector.find_candidates(
    placeholder_type="generic_panel",
    requirements=design_requirements
)

# Replace placeholder with real component
result = await component_selector.replace_placeholder(
    session_id=session_id,
    placeholder_id="placeholder_panel_0",
    real_component=selected_candidate
)
```

### 3. Iterative Refinement

Users can:
- Start with placeholder design for rapid prototyping
- Upload component datasheets as they become available
- Gradually replace placeholders with real components
- Maintain design connectivity throughout the process

## API Endpoints

### Create Session
```http
POST /api/v1/odl/sessions
Content-Type: application/json

{
  "session_id": "optional-custom-id"
}
```

### Analyze Placeholders
```http
GET /api/v1/odl/sessions/{session_id}/analysis

Response:
{
  "total_placeholders": 5,
  "placeholders_by_type": {
    "generic_panel": 2,
    "generic_inverter": 1,
    "generic_mount": 2
  },
  "completion_percentage": 20.0,
  "blocking_issues": ["Need panel components in library"],
  "available_replacements": {}
}
```

### Select Component
```http
POST /api/v1/odl/sessions/{session_id}/select-component
Content-Type: application/json

{
  "placeholder_id": "placeholder_panel_0",
  "component": {
    "part_number": "SP-400-XXX",
    "name": "SunPower 400W Panel",
    "category": "panel",
    "power": 400,
    "price": 250,
    "manufacturer": "SunPower"
  },
  "apply_to_all_similar": false
}
```

### Get ODL Text
```http
GET /api/v1/odl/sessions/{session_id}/text

Response:
{
  "text": "# OriginFlow ODL Design\n# Version: 1\n...",
  "version": 1,
  "node_count": 5,
  "edge_count": 4,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Frontend Integration

### ODL Code View

New layer in the canvas that shows live ODL text representation:

```tsx
// Usage in Workspace component
if (currentLayer === 'ODL Code') {
  return <ODLCodeView sessionId={currentSessionId || ''} />;
}
```

### Requirements Form

Enhanced form for entering design requirements:

```tsx
<RequirementsForm
  sessionId={sessionId}
  onSubmit={handleRequirementsSubmit}
  onCancel={handleCancel}
  initialValues={existingRequirements}
  isModal={true}
/>
```

### Component Selection Modal

Interactive component selection interface:

```tsx
<ComponentSelectionModal
  isOpen={isOpen}
  sessionId={sessionId}
  componentType="generic_panel"
  placeholderCount={2}
  options={availableComponents}
  onSelect={handleComponentSelect}
  onUploadMore={handleUploadMore}
/>
```

## Configuration

### Placeholder Defaults

Modify default values in `backend/services/placeholder_components.py`:

```python
PLACEHOLDER_COMPONENT_TYPES = {
    "generic_panel": PlaceholderComponent(
        type="generic_panel",
        default_attributes={
            "power": 400,  # Customize default power
            "voltage": 24,
            "efficiency": 0.2,
            # ... other attributes
        },
        # ... rest of configuration
    )
}
```

### Validation Rules

Add custom validation rules:

```python
validation_rules = {
    "required_attributes": ["power", "voltage"],
    "power_tolerance": 0.1,  # ±10%
    "voltage_compatibility": [12, 24, 48],
    "min_efficiency": 0.15  # 15% minimum
}
```

## Best Practices

### 1. Start with Requirements
Always define basic requirements (target power, roof area, budget) before generating placeholder designs.

### 2. Use Reasonable Defaults
Placeholder components use conservative defaults that work for most residential installations.

### 3. Gradual Replacement
Replace placeholders incrementally as real component data becomes available.

### 4. Validate Replacements
The system automatically validates that replacement components are technically compatible.

### 5. Maintain History
All placeholder replacements are tracked with timestamps and reasoning for audit purposes.

## Troubleshooting

### Common Issues

1. **No Candidates Found**
   - Upload more component datasheets
   - Check component categories match placeholder types
   - Verify requirements are reasonable

2. **Validation Errors**
   - Review component specifications
   - Check voltage/power compatibility
   - Ensure all required attributes are present

3. **Session Not Found**
   - Create new ODL session via API
   - Check session ID is valid
   - Verify backend connectivity

### Error Codes

- `404`: Session not found
- `400`: Invalid component data
- `409`: Version conflict (concurrent modifications)
- `500`: Server error during replacement

## Extension Points

### Adding New Placeholder Types

1. Define in `PLACEHOLDER_COMPONENT_TYPES`
2. Add validation rules
3. Update replacement categories
4. Test with real components

### Custom Sizing Logic

Override sizing methods in `PlaceholderComponentService`:

```python
def estimate_sizing(self, component_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
    # Custom sizing logic here
    pass
```

### Domain-Specific Agents

Create new agents that leverage the placeholder system for specialized domains (HVAC, lighting, etc.).

## Metrics and Analytics

The system tracks:
- Placeholder usage patterns
- Replacement success rates
- Time from placeholder to real component
- Design iteration cycles
- Component selection preferences

This data helps improve default values and recommendation algorithms over time.
