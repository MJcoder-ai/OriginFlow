/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace with fixes for component dragging, selection, and port connections.
*/
import React, { useState, useEffect } from 'react';
import {
  DndContext,
  useDroppable,
  useDraggable,
  DragEndEvent,
} from '@dnd-kit/core';
import { useAppStore, CanvasComponent, Port } from '../appStore';
import { PALETTE_COMPONENT_DRAG_TYPE } from './ComponentPalette';
import LinkLayer from './LinkLayer';
import clsx from 'clsx';

/** A component card rendered on the canvas with a connection handle */
const PortHandle: React.FC<{
  id: string;
  port: Port;
  isPending: boolean;
  onMouseDown: (portId: Port['id'], e: React.MouseEvent) => void;
  onMouseUp: (portId: Port['id'], e: React.MouseEvent) => void;
}> = ({ id, port, isPending, onMouseDown, onMouseUp }) => {
  const isInput = port.type === 'in';
  return (
    <div
      id={id}
      onMouseDown={(e) => {
        // Stop the card drag from starting when beginning a link
        e.stopPropagation();
        onMouseDown(port.id, e);
      }}
      onMouseUp={(e) => {
        e.stopPropagation();
        onMouseUp(port.id, e);
      }}
      className={clsx(
        'absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 border-white cursor-crosshair z-10 transition-transform',
        {
          ' -left-2 bg-green-400': isInput,
          ' -right-2 bg-red-400': !isInput,
          'transform scale-150 shadow-lg': isPending,
        }
      )}
    />
  );
};

const CanvasCard: React.FC<{
  component: CanvasComponent;
  isPendingLinkSource: boolean;
  onStartLink: (componentId: string, portId: Port['id']) => void;
  onEndLink: (componentId: string, portId: Port['id']) => void;
}> = ({ component, isPendingLinkSource, onStartLink, onEndLink }) => {
  const { selectedComponentId, selectComponent, deleteComponent } = useAppStore();
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
      onClick={() => selectComponent(component.id)}
      onContextMenu={(e) => {
        e.preventDefault();
        if (
          window.confirm(`Are you sure you want to delete "${component.name}"?`)
        ) {
          deleteComponent(component.id);
        }
      }}
      className={clsx(
        'absolute h-24 w-32 bg-white border-2 rounded-lg shadow-sm flex flex-col items-center justify-center p-2 cursor-grab',
        {
          'border-blue-500 ring-2 ring-blue-500': isSelected,
          'border-gray-300': !isSelected,
        }
      )}
    >
      {/* The main draggable area */}
      <div
        {...listeners}
        {...attributes}
        className="w-full h-full cursor-grab"
      />

      {/* Static content inside */}
      <div className="absolute top-0 left-0 w-full h-full flex flex-col items-center justify-center pointer-events-none">
        <span className="text-sm font-bold">{component.name}</span>
        <span className="text-xs text-gray-500">{component.type}</span>
      </div>

      {/* Render ports */}
      {component.ports.map((port) => (
        <PortHandle
          key={port.id}
          id={`port_${component.id}_${port.id}`}
          port={port}
          isPending={isPendingLinkSource && port.id === 'output'}
          onMouseDown={(portId) => onStartLink(component.id, portId)}
          onMouseUp={(portId) => onEndLink(component.id, portId)}
        />
      ))}
    </div>
  );
};

/** The main canvas area that is a droppable target */
const CanvasArea: React.FC<{
  pendingLinkSourceId: string | null;
  onStartLink: (sourceId: string, portId: Port['id']) => void;
  onEndLink: (targetId: string, portId: Port['id']) => void;
}> = ({ pendingLinkSourceId, onStartLink, onEndLink }) => {
  const { setNodeRef } = useDroppable({ id: 'canvas-area' });
  const components = useAppStore((state) => state.canvasComponents);

  return (
    <div className="flex-grow h-full relative">
      <div
        ref={setNodeRef}
        className="canvas-area-container w-full h-full border-2 border-dashed border-gray-300 rounded-lg"
      >
        {components.map((comp) => (
          <CanvasCard
            key={comp.id}
            component={comp}
            isPendingLinkSource={pendingLinkSourceId === comp.id}
            onStartLink={onStartLink}
            onEndLink={onEndLink}
          />
        ))}
      </div>
    </div>
  );
};

/** A visual element for resizing the panel */
export const Resizer: React.FC = () => (
    // For simplicity, we remove the resizing logic for now to focus on the link feature
    <div className="w-1.5 bg-gray-200"></div>
);

/** Primary workspace container */
const Workspace: React.FC = () => {
  const {
    addComponent,
    updateComponentPosition,
    addLink,
    fetchProject,
    selectedComponentId,
    deleteComponent,
  } = useAppStore();
  const componentCount = useAppStore((s) => s.canvasComponents.length);
  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        (event.key === 'Delete' || event.key === 'Backspace') &&
        selectedComponentId
      ) {
        deleteComponent(selectedComponentId);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedComponentId, deleteComponent]);
  const [pendingLink, setPendingLink] = useState<{ sourceId: string; portId: 'output' } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over, delta } = event;

    if (active.id && over && delta.x !== 0 && delta.y !== 0) {
      if (
        over.id === 'canvas-area' &&
        active.data.current?.type === PALETTE_COMPONENT_DRAG_TYPE
      ) {
        const ctype = active.data.current?.componentType;
        if (ctype) {
          addComponent({
            name: `${ctype} ${componentCount + 1}`,
            type: ctype,
            standard_code: `CODE-${Date.now()}`,
            x: 100,
            y: 100,
          });
        }
      } else if (
        over.id === 'canvas-area' &&
        active.data.current?.type === 'file-asset'
      ) {
        const asset = active.data.current?.asset;
        if (asset) {
          addComponent({
            name: asset.name,
            type: 'Datasheet',
            standard_code: `CODE-${Date.now()}`,
            x: 100,
            y: 100,
          });
        }
      } else if (active.data.current?.type !== PALETTE_COMPONENT_DRAG_TYPE) {
        updateComponentPosition(active.id as string, delta);
      }
    }
  };

  const handleStartLink = (sourceId: string, portId: Port['id']) => {
    if (portId === 'output') {
      setPendingLink({ sourceId, portId });
    }
  };

  const handleEndLink = async (targetId: string, portId: Port['id']) => {
    if (pendingLink && portId === 'input' && pendingLink.sourceId !== targetId) {
      await addLink({
        source_id: pendingLink.sourceId,
        target_id: targetId,
      });
    }
    setPendingLink(null);
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (pendingLink) {
      const rect = e.currentTarget.getBoundingClientRect();
      setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    }
  };

  const handleCanvasMouseUp = () => {
    setPendingLink(null);
  };



  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="flex-grow h-full relative" onMouseMove={handleCanvasMouseMove} onMouseUp={handleCanvasMouseUp}>
        <LinkLayer pendingLink={pendingLink} mousePos={mousePos} />
        <CanvasArea
          pendingLinkSourceId={pendingLink?.sourceId ?? null}
          onStartLink={handleStartLink}
          onEndLink={handleEndLink}
        />
      </div>
    </DndContext>
  );
};

export default Workspace;
