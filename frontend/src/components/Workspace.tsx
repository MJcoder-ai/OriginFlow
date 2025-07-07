/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace area housing the engineering canvas and properties panel.
 */
import React from 'react';
import PropertiesPanel from './PropertiesPanel';

/** A placeholder for the main canvas area */
const CanvasArea: React.FC = () => (
  <div className="flex-grow h-full border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center text-gray-400">
    Canvas Area
  </div>
);

/** A visual element for resizing the panel */
const Resizer: React.FC = () => (
  <div className="w-1.5 cursor-col-resize bg-gray-200 hover:bg-blue-500 transition-colors"></div>
);

/** Primary workspace container */
const Workspace: React.FC = () => (
  <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
    <CanvasArea />
    <Resizer />
    <PropertiesPanel />
  </main>
);

export default Workspace;
