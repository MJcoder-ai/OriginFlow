/**
 * File: frontend/src/components/PropertiesPanel.tsx
 * The main right-hand panel containing the component palette and chat interface.
 * Displays properties of the currently selected component on the canvas.
 * Enables editing of component names and provides an embedded chat.
*/
import React from 'react';
import { useAppStore } from '../appStore';
import ComponentPalette from './ComponentPalette';
import ChatPanel from './ChatPanel';

const PropertiesEditor: React.FC = () => {
  const { selectedComponentId, canvasComponents, updateComponentName } = useAppStore();

  const selectedComponent = canvasComponents.find((c) => c.id === selectedComponentId);

  if (!selectedComponent) {
    return (
      <div className="p-4 text-sm text-gray-500">
        Select a component on the canvas to see its properties.
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <h3 className="font-bold border-b pb-2">Properties</h3>
      <div>
        <label className="text-xs font-semibold text-gray-600 block mb-1">ID</label>
        <div className="text-xs p-2 bg-gray-100 rounded-md text-gray-500 select-all">
          {selectedComponent.id}
        </div>
      </div>
      <div>
        <label className="text-xs font-semibold text-gray-600 block mb-1">Type</label>
        <div className="text-sm p-2 bg-gray-100 rounded-md">
          {selectedComponent.type}
        </div>
      </div>
      <div>
        <label htmlFor="componentName" className="text-xs font-semibold text-gray-600 block mb-1">
          Name
        </label>
        <input
          id="componentName"
          type="text"
          value={selectedComponent.name}
          onChange={(e) => updateComponentName(selectedComponent.id, e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
      </div>
    </div>
  );
};

/** Container for palette and chat sections. */
const PropertiesPanel: React.FC = () => {
  return (
    // Main container uses flex column and fills available height
    <div className="w-full h-full bg-white border-l border-gray-200 flex flex-col">
      {/* Palette should not grow so the chat panel gets remaining space */}
      <div className="flex-shrink-0">
        <ComponentPalette />
      </div>

      {/* Properties editor also has fixed height */}
      <div className="flex-shrink-0 border-y">
        <PropertiesEditor />
      </div>

      {/* The chat wrapper grows and enables scrolling for the chat history */}
      <div className="flex-grow min-h-0">
        <ChatPanel />
      </div>
    </div>
  );
};

export default PropertiesPanel;
