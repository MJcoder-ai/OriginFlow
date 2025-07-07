/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace housing the canvas, properties panel, and their interaction logic.
 * Implements component placement and selection highlighting.
 * Handles component selection and highlights the active element.
*/
import React, { useState } from 'react';
import {
  DndContext,
  useDroppable,
  useDraggable,
  DragEndEvent,
} from '@dnd-kit/core';
import { useAppStore, CanvasComponent, Port } from '../appStore';
import PropertiesPanel from './PropertiesPanel';
import LinkLayer from './LinkLayer';
import clsx from 'clsx';

/** A component card rendered on the canvas with a connection handle */
const PortHandle: React.FC<{
  componentId: string;
  port: Port;
  onMouseDown: (componentId: string, portId: Port['id'], e: React.MouseEvent) => void;
  onMouseUp: (componentId: string, portId: Port['id'], e: React.MouseEvent) => void;
}> = ({ componentId, port, onMouseDown, onMouseUp }) => {
  const isInput = port.type === 'in';
  return (
    <div
      id={`port_${componentId}_${port.id}`}
      onMouseDown={(e) => {
        e.stopPropagation();
        onMouseDown(componentId, port.id, e);
      }}
      onMouseUp={(e) => {
        e.stopPropagation();
        onMouseUp(componentId, port.id, e);
      }}
      className={clsx(
        'absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white cursor-crosshair',
        {
          ' -left-2 bg-green-400': isInput,
          ' -right-2 bg-red-400': !isInput,
        }
      )}
    />
  );
};

const CanvasCard: React.FC<{
  component: CanvasComponent;
  onStartLink: (sourceId: string, portId: Port['id'], e: React.MouseEvent) => void;
  onEndLink: (targetId: string, portId: Port['id'], e: React.MouseEvent) => void;
}> = ({ component, onStartLink, onEndLink }) => {
  const { selectedComponentId, selectComponent } = useAppStore();
  const isSelected = selectedComponentId === component.id;

  // Enable dragging of the card itself
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: component.id,
  });

  // Apply transform during drag while keeping absolute positioning
  const style = {
    top: component.y,
    left: component.x,
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    position: 'absolute' as const,
  };

  return (
    <div
      id={`component-card-${component.id}`}
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={() => selectComponent(component.id)}
      className={clsx(
        'h-24 w-32 bg-white border-2 rounded-lg shadow-sm flex flex-col items-center justify-center p-2 cursor-grab active:cursor-grabbing absolute',
        {
          'border-blue-500 ring-2 ring-blue-500': isSelected,
          'border-gray-300': !isSelected,
        }
      )}
    >
      <span className="text-sm font-bold">{component.name}</span>
      <span className="text-xs text-gray-500">{component.type}</span>
      {component.ports.map((port) => (
        <PortHandle
          key={port.id}
          componentId={component.id}
          port={port}
          onMouseDown={onStartLink}
          onMouseUp={onEndLink}
        />
      ))}
    </div>
  );
};

/** The main canvas area that is a droppable target */
const CanvasArea: React.FC<{
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: () => void;
  onStartLink: (sourceId: string, portId: Port['id'], e: React.MouseEvent) => void;
  onEndLink: (targetId: string, portId: Port['id'], e: React.MouseEvent) => void;
}> = ({ onMouseMove, onMouseUp, onStartLink, onEndLink }) => {
  const { setNodeRef } = useDroppable({ id: 'canvas-area' });
  const components = useAppStore((state) => state.canvasComponents);

  return (
    <div className="flex-grow h-full relative">
      <div
        ref={setNodeRef}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        className="canvas-area-container w-full h-full border-2 border-dashed border-gray-300 rounded-lg"
      >
        {components.map((comp) => (
          <CanvasCard
            key={comp.id}
            component={comp}
            onStartLink={onStartLink}
            onEndLink={onEndLink}
          />
        ))}
      </div>
    </div>
  );
};

/** A visual element for resizing the panel */
const Resizer: React.FC = () => (
    // For simplicity, we remove the resizing logic for now to focus on the link feature
    <div className="w-1.5 bg-gray-200"></div>
);

/** Primary workspace container */
const Workspace: React.FC = () => {
  const { addComponent, updateComponentPosition, addLink } = useAppStore();
  const [pendingLink, setPendingLink] = useState<{ sourceId: string; portId: 'output' } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over, delta } = event;

    if (over && over.id === 'canvas-area') {
      if (String(active.id).startsWith('palette-')) {
        const componentType = active.data.current?.type;
        if (componentType) {
          addComponent(componentType);
        }
      } else {
        updateComponentPosition(active.id as string, delta);
      }
    } else if (!String(active.id).startsWith('palette-')) {
      updateComponentPosition(active.id as string, delta);
    }
  };

  const handleStartLink = (sourceId: string, portId: Port['id']) => {
    if (portId === 'output') {
      setPendingLink({ sourceId, portId });
    }
  };

  const handleEndLink = (targetId: string, portId: Port['id']) => {
    if (pendingLink && portId === 'input') {
      addLink({
        source: { componentId: pendingLink.sourceId, portId: pendingLink.portId },
        target: { componentId: targetId, portId: 'input' },
      });
    }
    setPendingLink(null);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
        <div className="flex-grow h-full relative">
          <LinkLayer pendingLink={pendingLink} mousePos={mousePos} />
          <CanvasArea
            onMouseMove={handleMouseMove}
            onMouseUp={() => setPendingLink(null)}
            onStartLink={handleStartLink}
            onEndLink={handleEndLink}
          />
        </div>
        <Resizer />
        <div className="w-[300px]">
          <PropertiesPanel />
        </div>
      </main>
    </DndContext>
  );
};

export default Workspace;
