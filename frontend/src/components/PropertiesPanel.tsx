/**
 * File: frontend/src/components/PropertiesPanel.tsx
 * The main right-hand panel containing the component palette and chat interface.
 * Displays properties of the currently selected component on the canvas.
 * Enables editing of component names and provides an embedded chat.
*/
import React from 'react';
import { useAppStore } from '../appStore';

const PropertiesEditor: React.FC = () => {
  const { selectedComponentId, canvasComponents, updateComponentName } = useAppStore();

  const selectedComponent = canvasComponents.find((c) => c.id === selectedComponentId);

  if (!selectedComponent) return null;

  return (
    <aside
      className="w-full max-h-[250px] p-4 border-b bg-white shadow transition-all"
      role="dialog"
      aria-label="Component Properties"
    >
      <h2 className="text-sm font-semibold text-gray-800 mb-2">
        Properties: {selectedComponent.name || 'Unnamed'}
      </h2>

      <form className="flex flex-col gap-3 text-sm">
        <label className="flex flex-col">
          ID
          <input
            type="text"
            value={selectedComponent.id}
            disabled
            className="mt-1 p-1 border rounded bg-gray-100 text-gray-500"
          />
        </label>

        <label className="flex flex-col">
          Name
          <input
            type="text"
            defaultValue={selectedComponent.name}
            className="mt-1 p-1 border rounded"
            onBlur={(e) => {
              updateComponentName(selectedComponent.id, e.target.value);
            }}
          />
        </label>

        <label className="flex flex-col">
          Type
          <input
            type="text"
            value={selectedComponent.type}
            disabled
            className="mt-1 p-1 border rounded bg-gray-100 text-gray-500"
          />
        </label>
      </form>
    </aside>
  );
};

/** Container for palette and chat sections. */
const PropertiesPanel: React.FC = () => {
  return <PropertiesEditor />;
};

export default PropertiesPanel;
