/**
 * File: frontend/src/components/ComponentPalette.tsx
 * Displays a list of components that can be dragged onto the canvas.
 * Uses `@dnd-kit/core` to provide drag sources for the workspace.
 */
import React from 'react';
import { useDraggable } from '@dnd-kit/core';

/** Available component types presented in the palette. */
const PALETTE_ITEMS = ['Panel', 'Inverter', 'Battery', 'JunctionBox'];

/** Small wrapper representing a palette item that can be dragged. */
const PaletteItem: React.FC<{ type: string }> = ({ type }) => {
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `palette-${type}`,
    data: { type },
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className="h-12 bg-gray-100 rounded-md flex items-center justify-center text-sm text-gray-700 select-none cursor-grab active:cursor-grabbing"
    >
      {type}
    </div>
  );
};

/** The palette showing available draggable component types. */
const ComponentPalette: React.FC = () => {
  return (
    <div className="p-2 border-b border-gray-200">
      <div className="grid grid-cols-2 gap-2">
        {PALETTE_ITEMS.map((type) => (
          <PaletteItem key={type} type={type} />
        ))}
      </div>
    </div>
  );
};

export default ComponentPalette;
