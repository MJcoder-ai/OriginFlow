import React from 'react';
import { Server, PanelTop, Battery, Boxes, Cable } from 'lucide-react';
import { useDraggable } from '@dnd-kit/core';

export const PALETTE_COMPONENT_DRAG_TYPE = 'palette-component';

const paletteItems = [
  { type: 'Panel', icon: PanelTop, label: 'Panel' },
  { type: 'Inverter', icon: Server, label: 'Inverter' },
  { type: 'Battery', icon: Battery, label: 'Battery' },
  { type: 'JunctionBox', icon: Boxes, label: 'JunctionBox' },
  { type: 'Cable', icon: Cable, label: 'Cable' },
];

const PaletteItem: React.FC<{ item: (typeof paletteItems)[0] }> = ({ item }) => {
  const Icon = item.icon;
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `palette-${item.type}`,
    data: { type: PALETTE_COMPONENT_DRAG_TYPE, componentType: item.type },
  });

  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className="flex flex-col items-center p-2 border rounded-md shadow-sm bg-white cursor-grab hover:bg-gray-50"
    >
      <Icon size={32} className="mb-2" />
      <span className="text-xs text-center">{item.label}</span>
    </div>
  );
};

export const ComponentPalette: React.FC = () => {
  return (
    <div className="p-2 grid grid-cols-2 gap-2">
      {paletteItems.map((item) => (
        <PaletteItem key={item.type} item={item} />
      ))}
    </div>
  );
};

export default ComponentPalette;
