# Frontend Enhancements

## Overview

The frontend enhancements transform OriginFlow from a traditional CAD tool into an intelligent, iterative design platform. Key additions include the ODL Code View, enhanced requirements management, component selection interfaces, and improved planning visualization.

## New Components

### 1. ODL Code View (`ODLCodeView.tsx`)

**Purpose**: Live textual representation of the design in ODL format

**Features**:
- Real-time ODL code generation
- Auto-refresh capabilities
- Copy to clipboard functionality
- Download as file
- Syntax highlighting for ODL format
- Version tracking and statistics

**Usage**:
```tsx
<ODLCodeView sessionId={sessionId} />
```

**Key Features**:
- **Live Updates**: Automatically refreshes every 5 seconds
- **Manual Control**: Toggle auto-refresh on/off
- **Export Options**: Copy to clipboard or download as .txt file
- **Statistics**: Shows version, node count, edge count, and line count
- **Error Handling**: Graceful fallback when session unavailable

**Integration**:
Added as new layer "ODL Code" in the main workspace canvas. The view reflects the same session used for design tasks.

### 2. Requirements Form (`RequirementsForm.tsx`)

**Purpose**: Comprehensive form for entering and editing design requirements

**Features**:
- Basic requirements (power, area, budget)
- Backup power specifications
- Brand preferences
- Advanced environmental conditions
- Real-time validation
- Modal and inline modes

**Required Fields**:
- **Target Power**: System power output in Watts
- **Roof Area**: Available space in square meters  
- **Budget**: Total project budget in dollars

**Optional Fields**:
- **Backup Hours**: Required backup power duration
- **Preferred Brands**: Comma-separated brand list
- **Climate Zone**: Environmental classification
- **Wind Speed**: Maximum wind speed rating
- **Snow Load**: Snow load requirements

**Validation Rules**:
```typescript
// Power validation
if (!requirements.target_power || requirements.target_power <= 0) {
  errors.target_power = 'Target power must be greater than 0';
} else if (requirements.target_power > 1000000) {
  errors.target_power = 'Target power seems unreasonably high';
}

// Budget validation  
if (requirements.budget < 1000) {
  errors.budget = 'Budget may be too low for a solar system';
}
```

**Usage**:
```tsx
<RequirementsForm
  sessionId={sessionId}
  onSubmit={handleSubmit}
  onCancel={handleCancel}
  initialValues={existingRequirements}
  isModal={true}
/>
```

### 3. Component Selection Modal (`ComponentSelectionModal.tsx`)

**Purpose**: Interactive interface for selecting real components to replace placeholders

**Features**:
- Component filtering and sorting
- Suitability scoring display
- Bulk selection options
- Real-time availability checking
- Detailed component comparison

**Filter Options**:
- **Sort By**: Best match, price, power, efficiency
- **Manufacturer**: Filter by brand
- **Power Range**: Min/max power filtering
- **Price Range**: Budget-based filtering

**Component Display**:
```typescript
interface ComponentOption {
  part_number: string;
  name: string;
  power?: number;
  price?: number;
  manufacturer?: string;
  efficiency?: number;
  suitability_score?: number;
  availability?: boolean;
  category?: string;
}
```

**Suitability Scoring**:
- **Green (80%+)**: Excellent match
- **Yellow (60-79%)**: Good match  
- **Red (<60%)**: Poor match

**Usage**:
```tsx
<ComponentSelectionModal
  isOpen={showModal}
  sessionId={sessionId}
  componentType="generic_panel"
  placeholderCount={3}
  options={availableComponents}
  onSelect={handleComponentSelect}
  onUploadMore={showUploadModal}
/>
```

### 4. Enhanced Plan Timeline (`EnhancedPlanTimeline.tsx`)

**Purpose**: Advanced visualization and control of the design planning process

**Features**:
- Real-time task status updates
- Progress indicators
- Context-aware action buttons
- Auto-refresh capabilities
- Quick actions bar

**Task Status Indicators**:
- ✅ **Complete**: Task finished successfully
- ⏳ **In Progress**: Task currently executing  
- 📋 **Pending**: Ready to execute
- 🚫 **Blocked**: Waiting for prerequisites

**Enhanced Task Display**:
```typescript
interface PlanTask {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'complete' | 'blocked';
  reason?: string;
  estimated_panels?: number;
  estimated_inverters?: number;
  placeholder_summary?: string;
  design_completeness?: number;
  missing_requirements?: string[];
  missing_components?: string[];
}
```

**Auto-Refresh**: Updates task list every 10 seconds to reflect current system state

**Quick Actions**:
- 📋 Edit Requirements
- 📁 Upload Components  
- 🔄 Refresh Plan

**Usage**:
```tsx
<EnhancedPlanTimeline
  sessionId={sessionId}
  tasks={planTasks}
  onRunTask={executeTask}
  onShowRequirements={showRequirementsForm}
  onUploadComponents={showUploadModal}
  onShowComponentSelection={showComponentSelection}
/>
```

## App Store Enhancements

### ODL Session Management

The ODL Code View reuses the application's primary `sessionId`. There is no separate
`currentSessionId` and sessions are not created automatically when switching layers.
If a session does not yet exist, it will be created when a design command is executed via
`analyzeAndExecute` or by calling `createOdlSession()` directly.

All user commands are routed through the analysis endpoint, allowing the router agent to
classify intent (design vs. component vs. wiring) and return the appropriate `AiAction`
set without relying on brittle keyword checks.

### Layer Management Updates

**Enhanced Layer List**:
```typescript
layers: [
  'Single-Line Diagram',
  'High-Level Overview', 
  'Civil/Structural',
  'Networking/Monitoring',
  'ODL Code'  // New layer
]
```

**Layer Selection**:
```typescript
setCurrentLayer: (layer) => {
  set({ currentLayer: layer });
  // The ODL Code View reads the existing design session (sessionId).
  // No new session is created on layer switch.
}
```

## Workspace Integration

### Layer-Aware Rendering

**Enhanced Workspace Component**:
```tsx
const renderLayerContent = () => {
  if (currentLayer === 'ODL Code') {
    return <ODLCodeView sessionId={sessionId} />;
  }

  // Default canvas for other layers
  return (
    <>
      <LinkLayer pendingLink={pendingLink} mousePos={mousePos} />
      <CanvasArea
        pendingLinkSourceId={pendingLink?.sourceId ?? null}
        onStartLink={handleStartLink}
        onEndLink={handleEndLink}
      />
    </>
  );
};
```

### State Management Integration

  **Session State Synchronization**:
  - Session ID persistence across page reloads
  - Graceful handling of session expiration

## User Experience Enhancements

### 1. Progressive Disclosure

**Beginner Flow**:
1. Enter basic requirements (power, area, budget)
2. Generate placeholder design
3. Review ODL representation
4. Upload components as available
5. Replace placeholders incrementally

**Advanced Flow**:
1. Upload all components first
2. Define detailed requirements
3. Generate optimized design
4. Fine-tune with structural/wiring details

### 2. Context-Aware Actions

**Smart Action Buttons**:
- **Blocked Tasks**: Show "Fix Issues" or "Enter Requirements"
- **Pending Tasks**: Show "Run Task" or "Select Components"
- **Placeholder Tasks**: Show "Select Components" button

**Dynamic Help Text**:
- Missing requirements highlighted in red
- Available actions suggested in task descriptions
- Progress indicators show completion status

### 3. Error Handling

**Graceful Degradation**:
```tsx
// Fallback when session unavailable
if (!sessionId) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="text-gray-500 mb-2">No active session</div>
        <div className="text-sm text-gray-400">
          Start designing to see ODL code
        </div>
      </div>
    </div>
  );
}
```

**Error Recovery**:
- Automatic retry on network failures
- Clear error messages with suggested actions
- Fallback content when data unavailable

### 4. Performance Optimizations

**Efficient Updates**:
- Debounced auto-refresh to prevent excessive API calls
- Conditional rendering based on layer selection
- Lazy loading of component options

**Memory Management**:
- Cleanup of intervals on component unmount
- Efficient state updates using Zustand
- Minimal re-renders with proper dependency arrays

## Styling and Theming

### Consistent Design Language

**Color Scheme**:
- **Primary**: Blue (#3B82F6) for actions and highlights
- **Success**: Green (#10B981) for completed states
- **Warning**: Orange (#F59E0B) for blocked states  
- **Error**: Red (#EF4444) for critical issues
- **Neutral**: Gray scale for backgrounds and text

**Component Styling**:
```css
/* Task status indicators */
.status-complete { @apply text-green-600 bg-green-100 border-green-200; }
.status-pending { @apply text-blue-600 bg-blue-100 border-blue-200; }
.status-blocked { @apply text-red-600 bg-red-100 border-red-200; }

/* Action buttons */
.btn-primary { @apply bg-blue-600 text-white hover:bg-blue-700; }
.btn-secondary { @apply bg-gray-200 text-gray-700 hover:bg-gray-300; }
```

### Responsive Design

**Mobile-First Approach**:
- Grid layouts adapt to screen size
- Touch-friendly button sizes
- Collapsible sections for small screens

**Tablet Optimization**:
- Optimized modal sizes
- Side-by-side layouts where appropriate
- Touch and mouse interaction support

## Integration Points

### Backend API Consumption

**Requirements Management**:
```typescript
// Update requirements
const updateRequirements = async (requirements: DesignRequirements) => {
  const response = await fetch(`${API_BASE_URL}/odl/sessions/${sessionId}/requirements`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requirements })
  });
  return response.json();
};
```

**Component Selection**:
```typescript
// Select component
const selectComponent = async (placeholderId: string, component: ComponentCandidate) => {
  const response = await fetch(`${API_BASE_URL}/odl/sessions/${sessionId}/select-component`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ placeholder_id: placeholderId, component })
  });
  return response.json();
};
```

**ODL Text Retrieval**:
```typescript
// Get ODL representation
const getODLText = async (sessionId: string) => {
  const response = await fetch(`${API_BASE_URL}/odl/sessions/${sessionId}/text`);
  return response.json();
};
```

### Real-Time Updates

**WebSocket Integration** (Future Enhancement):
```typescript
// Real-time graph updates
const ws = new WebSocket(`ws://localhost:8000/ws/odl/${sessionId}`);
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Update UI with real-time changes
};
```

## Testing Strategy

### Component Testing

**Unit Tests**:
```typescript
// Example test for RequirementsForm
describe('RequirementsForm', () => {
  it('validates required fields', () => {
    render(<RequirementsForm {...props} />);
    fireEvent.click(screen.getByText('Save Requirements'));
    expect(screen.getByText('Target power must be greater than 0')).toBeInTheDocument();
  });
});
```

**Integration Tests**:
- Form submission workflows
- Component selection process  
- ODL session lifecycle

### User Experience Testing

**Accessibility**:
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

**Performance**:
- Load time optimization
- Memory usage monitoring
- Network request efficiency

## Future Enhancements

### 1. Advanced Visualization

**3D Canvas Integration**:
- 3D representation of designs
- Interactive component placement
- Solar irradiance visualization

**Enhanced ODL Syntax**:
- Syntax highlighting
- Auto-completion
- Error underlining

### 2. Collaboration Features

**Multi-User Support**:
- Real-time collaborative editing
- User presence indicators
- Change attribution

**Comments and Annotations**:
- Design review workflow
- Inline comments on components
- Approval/rejection system

### 3. Mobile Application

**Native Mobile Apps**:
- Field data collection
- Photo integration
- Offline design capability

### 4. AI-Powered Assistance

**Smart Suggestions**:
- Automated component recommendations
- Design optimization hints
- Cost optimization suggestions

**Natural Language Interface**:
- Voice commands for design modifications
- Conversational requirement gathering
- Automated report generation

## Migration Guide

### From Legacy Interface

1. **Update Component Imports**: Add new component imports
2. **Extend App Store**: Add ODL session management
3. **Update Layer Logic**: Integrate ODL Code View
4. **Add Route Handlers**: Wire up new modal and form interactions

### Backward Compatibility

All existing functionality remains intact. New features are additive and gracefully degrade when backend features are unavailable.
