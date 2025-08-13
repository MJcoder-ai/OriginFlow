# Enhanced Dynamic Planner

## Overview

The Enhanced Dynamic Planner represents a significant evolution of OriginFlow's task orchestration system. It introduces placeholder-aware planning, multi-domain support, and adaptive task generation based on real-time design state analysis.

## Architecture Evolution

### Original Planner
- Static task sequences
- Basic requirement checking
- Limited to core PV design tasks

### Enhanced Planner
- **Dynamic State Analysis**: Deep inspection of graph state including placeholder detection
- **Conditional Task Logic**: Tasks appear/disappear based on design progress
- **Multi-Domain Support**: Battery, monitoring, and future domain integration
- **Placeholder Awareness**: Different task flows for placeholder vs. real components
- **Context-Rich Planning**: Enhanced task metadata with progress indicators

## Core Components

### 1. Graph State Analyzer (`_analyze_graph_state`)

Performs comprehensive analysis of the current design:

```python
state = {
    "has_panels": bool,
    "has_inverters": bool, 
    "has_mounts": bool,
    "has_wiring": bool,
    "has_batteries": bool,
    "has_monitoring": bool,
    "panel_count": int,
    "inverter_count": int,
    "has_preliminary_design": bool,
    "has_placeholders": bool,
    "placeholders_by_type": Dict[str, int],
    "total_placeholders": int,
    "placeholder_percentage": float,
    "real_component_count": int,
    "requirements_complete": bool,
    "components_available": bool,
    "allow_placeholder_design": bool,
    "available_replacement_count": int
}
```

### 2. Enhanced Task Types

#### Standard Tasks (Enhanced)
- **gather_requirements**: Now placeholder-aware
- **generate_design**: Supports both real and placeholder components
- **generate_structural**: Enhanced with placeholder mounting
- **generate_wiring**: Placeholder-aware cable/fuse generation
- **refine_validate**: Multi-domain validation

#### New Task Types
- **populate_real_components**: Replace placeholders with real parts
- **generate_battery**: Design battery storage systems
- **generate_monitoring**: Add system monitoring capabilities

### 3. Conditional Task Logic

Tasks now include rich conditional logic:

```python
# Example: Component population task only appears when needed
if state["has_placeholders"] and state["components_available"]:
    tasks.append({
        "id": "populate_real_components",
        "status": "pending",
        "reason": f"Replace {state['total_placeholders']} placeholder component(s)",
        "placeholder_summary": self._create_placeholder_summary(state["placeholders_by_type"]),
        "estimated_selections": state["total_placeholders"],
        "available_replacements": state.get("available_replacement_count", 0)
    })
```

## Task Generation Logic

### 1. Requirements Phase
```python
if not requirements_complete or (not components_available and not state["allow_placeholder_design"]):
    # Block until requirements are met OR placeholders are acceptable
    task = blocked_gather_requirements_task()
else:
    # Proceed with design
    task = complete_gather_requirements_task()
```

### 2. Design Generation Phase
```python
if not has_preliminary_design:
    if requirements_complete and (components_available or state["allow_placeholder_design"]):
        design_type = "real" if components_available else "placeholder"
        task = create_design_task(design_type)
    else:
        task = blocked_design_task()
```

### 3. Component Population Phase
```python
if state["has_placeholders"] and state["components_available"]:
    task = create_component_selection_task(
        placeholders=state["placeholders_by_type"],
        available_count=state["available_replacement_count"]
    )
```

### 4. Domain Expansion Phase
```python
# Battery system design
if has_preliminary_design and should_add_battery_design(requirements, state):
    task = create_battery_task(
        backup_hours=requirements.get("backup_hours", 8),
        estimated_capacity=estimate_battery_capacity(requirements)
    )

# Monitoring system design  
if has_preliminary_design and should_add_monitoring(requirements, state):
    task = create_monitoring_task(monitoring_type="basic")
```

## Enhanced Task Metadata

Each task now includes rich metadata for better UX:

```python
{
    "id": "generate_design",
    "title": "Generate Design", 
    "status": "pending",
    "reason": "Ready to generate placeholder design",
    "estimated_panels": 5,
    "estimated_inverters": 1,
    "design_type": "placeholder",
    "missing_requirements": [],
    "missing_components": [],
    "can_use_placeholders": True,
    "design_completeness": 0.6,
    "placeholder_percentage": 80.0
}
```

## Planning Strategies

### 1. Placeholder-First Strategy

When components aren't available:
1. Generate complete placeholder design
2. Validate design feasibility
3. Add structural and wiring placeholders
4. Present component selection options
5. Incrementally replace placeholders

### 2. Component-First Strategy

When components are available:
1. Generate design with real components
2. Add structural elements
3. Complete wiring design
4. Validate and optimize

### 3. Hybrid Strategy

Mix of placeholder and real components:
1. Use real components where available
2. Fill gaps with placeholders
3. Prioritize critical component selection
4. Maintain design connectivity

## API Integration

### Get Dynamic Plan
```http
GET /api/v1/odl/sessions/{session_id}/plan?command=design%20system

Response:
{
    "session_id": "uuid",
    "tasks": [
        {
            "id": "gather_requirements",
            "title": "Gather Requirements",
            "status": "complete",
            "reason": "All requirements collected"
        },
        {
            "id": "generate_design", 
            "title": "Generate Design",
            "status": "pending",
            "reason": "Ready to generate placeholder design",
            "design_type": "placeholder",
            "estimated_panels": 5,
            "estimated_inverters": 1
        }
    ],
    "total_tasks": 6,
    "completed_tasks": 1,
    "blocked_tasks": 0,
    "pending_tasks": 5
}
```

### Execute Task
```http
POST /api/v1/odl/sessions/{session_id}/act
Content-Type: application/json

{
    "task_id": "populate_real_components",
    "action": "select_components",
    "graph_version": 5
}
```

## Domain Agent Integration

### PVDesignAgent Enhancements
- Placeholder design generation
- Real component selection
- Hybrid design support
- Enhanced confidence scoring

### New ComponentSelectorAgent
- Candidate finding and ranking
- Bulk replacement operations
- Compatibility validation
- Selection history tracking

### Enhanced StructuralAgent
- Placeholder mounting generation
- Load calculation placeholders
- Material selection guidance

### Enhanced WiringAgent
- Placeholder cable sizing
- Protection device selection
- Voltage drop estimation

## Frontend Integration

### Enhanced Plan Timeline
```tsx
<EnhancedPlanTimeline
  sessionId={sessionId}
  tasks={planTasks}
  onRunTask={handleRunTask}
  onShowRequirements={showRequirementsForm}
  onUploadComponents={showUploadModal}
  onShowComponentSelection={showComponentSelection}
/>
```

Features:
- Real-time task status updates
- Progress indicators
- Action buttons for blocked tasks
- Quick actions bar
- Auto-refresh capabilities

### Task Status Indicators
- ✅ Complete: Task finished successfully
- ⏳ In Progress: Task currently executing
- 📋 Pending: Ready to execute
- 🚫 Blocked: Waiting for prerequisites

## Configuration

### Task Conditions
Configure when tasks should appear:

```python
def _should_add_battery_design(self, requirements: Dict[str, Any], state: Dict[str, Any]) -> bool:
    backup_hours = requirements.get("backup_hours", 0)
    return backup_hours > 0 and not state.get("has_batteries", False)
```

### Task Dependencies
Define task execution order:

```python
TASK_DEPENDENCIES = {
    "generate_structural": ["generate_design"],
    "generate_wiring": ["generate_design"],
    "populate_real_components": ["generate_design"],
    "refine_validate": ["generate_design"]
}
```

### Placeholder Thresholds
Control when to suggest component selection:

```python
COMPONENT_SELECTION_THRESHOLDS = {
    "min_placeholders": 1,
    "placeholder_percentage": 0.5,  # 50%
    "available_replacements": 1
}
```

## Best Practices

### 1. Progressive Disclosure
Start with essential tasks and progressively reveal advanced options based on design maturity.

### 2. Context-Aware Messaging
Provide specific, actionable guidance in task descriptions and blocking reasons.

### 3. Graceful Degradation
Always provide fallback options when preferred workflows are blocked.

### 4. State Synchronization
Keep task list synchronized with actual graph state through regular analysis.

### 5. User Choice Preservation
Allow users to skip or postpone tasks without breaking the overall flow.

## Performance Considerations

### State Analysis Caching
- Cache graph analysis results
- Invalidate on graph modifications
- Batch multiple state checks

### Task List Optimization
- Generate only visible tasks
- Lazy-load task details
- Debounce rapid updates

### Background Processing
- Pre-compute available replacements
- Asynchronous component searches
- Progressive enhancement

## Future Enhancements

### 1. Machine Learning Integration
- Predictive task suggestions
- Learned user preferences
- Automated component selection

### 2. Multi-User Collaboration
- Shared task ownership
- Parallel task execution
- Conflict resolution

### 3. Domain Expansion
- HVAC system integration
- Electrical panel design
- Load analysis automation

### 4. Advanced Validation
- Code compliance checking
- Cost optimization suggestions
- Performance predictions

## Troubleshooting

### Common Issues

1. **Tasks Not Appearing**
   - Check graph state analysis
   - Verify requirements completion
   - Review task conditions

2. **Stuck in Blocked State**
   - Upload component datasheets
   - Complete missing requirements
   - Check system dependencies

3. **Performance Issues**
   - Enable state caching
   - Reduce analysis frequency
   - Optimize database queries

### Debug Information

Enable detailed logging:
```python
import logging
logging.getLogger('backend.agents.planner_agent').setLevel(logging.DEBUG)
```

View state analysis:
```http
GET /api/v1/odl/sessions/{session_id}/analysis
```

## Migration Guide

### From Legacy Planner

1. **Update Task Handlers**: Ensure agents support new task metadata
2. **Add State Analysis**: Implement graph state checking
3. **Enable Placeholders**: Configure placeholder component support
4. **Update Frontend**: Integrate enhanced timeline component

### Backward Compatibility

The enhanced planner maintains compatibility with existing task IDs and basic functionality while adding new capabilities.
