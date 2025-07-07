/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace area for engineering canvas and other views.
 * Currently displays a placeholder panel.
 */
import React from 'react';

/** Primary workspace container. */
const Workspace: React.FC = () => (
  <main className="[grid-area:workspace] bg-gray-50 p-4 overflow-auto">
    <div className="h-full border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center text-gray-400">
      Workspace Area
    </div>
  </main>
);

export default Workspace;
