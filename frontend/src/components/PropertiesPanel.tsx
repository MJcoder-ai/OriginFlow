/**
 * File: frontend/src/components/PropertiesPanel.tsx
 * The main right-hand panel containing the component palette and chat interface.
 */
import React from 'react';
import ComponentPalette from './ComponentPalette';
import ChatPanel from './ChatPanel';

/** Container for palette and chat sections. */
const PropertiesPanel: React.FC = () => {
  return (
    <div className="w-[300px] min-w-[200px] max-w-[500px] bg-white border-l border-gray-200 flex flex-col">
      <ComponentPalette />
      <ChatPanel />
    </div>
  );
};

export default PropertiesPanel;
