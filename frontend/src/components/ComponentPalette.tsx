/**
 * File: frontend/src/components/ComponentPalette.tsx
 * Displays a list of components that can be dragged onto the canvas.
 * Drag-and-drop will be implemented in a later iteration.
 */
import React from 'react';

/** Small wrapper representing a palette item. */
const PaletteItem: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="h-12 bg-gray-100 rounded-md flex items-center justify-center text-sm text-gray-700 select-none cursor-grab">
    {children}
  </div>
);

/** The palette showing available draggable component types. */
const ComponentPalette: React.FC = () => {
  return (
    <div className="p-2 border-b border-gray-200">
      <div className="grid grid-cols-2 gap-2">
        <PaletteItem>PanelSection_1</PaletteItem>
        <PaletteItem>PanelSection_2</PaletteItem>
        <PaletteItem>PanelSection_3</PaletteItem>
        <PaletteItem>PanelSection_4</PaletteItem>
      </div>
    </div>
  );
};

export default ComponentPalette;
