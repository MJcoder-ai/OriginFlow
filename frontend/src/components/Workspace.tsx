/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace with fixes for component dragging, selection, and port connections.
*/
import React, { useState, useEffect } from 'react';
import {
  useDroppable,
  useDraggable,
} from '@dnd-kit/core';
import { useAppStore, CanvasComponent, Port } from '../appStore';
import LinkLayer from './LinkLayer';
import LayerSelector from './LayerSelector';
import SubAssemblyButton from './SubAssemblyButton';
import ODLCodeView from './ODLCodeView';
import clsx from 'clsx';
import { suggestLayout } from '../layout/LayoutManager';
import { routeEdgesElk } from '../layout/EdgeRouter';

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
    data: { type: 'canvas-card' },
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
  const currentLayer = useAppStore((state) => state.currentLayer);
  const allComponents = useAppStore((state) => state.canvasComponents);
  // Filter components based on the current layer.  Components without a
  // layer property belong to the default layer (Single-Line Diagram).
  const components = allComponents.filter(
    (comp) => !comp.layer || comp.layer === currentLayer
  );

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
    refreshGraphView,
    selectedComponentId,
    deleteComponent,
    currentLayer,
    sessionId, // Use the main sessionId for ODL view
    graphVersion,
    canvasComponents,
    links,
  } = useAppStore();
  useEffect(() => {
    refreshGraphView();
  }, [refreshGraphView, sessionId, currentLayer, graphVersion]);

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

  const onAutoLayout = async () => {
    const layerMap: Record<string, string> = {
      'Single-Line Diagram': 'single_line',
      'High-Level Overview': 'high_level',
      'Civil/Structural': 'civil',
      'Networking/Monitoring': 'networking',
      'ODL Code': 'physical',
    };
    const layerName = layerMap[currentLayer] || 'single_line';
    const nodes = canvasComponents.map((c) => ({
      id: c.id,
      width: 120,
      height: 72,
      layout: { [layerName]: { x: c.x, y: c.y } },
    }));
    const edges = links.map((l) => ({ id: l.id, source: l.source_id, target: l.target_id }));
    const locked: Record<string, boolean> = {};
    const positions = await suggestLayout(nodes, edges, layerName as any, locked);
    for (const [id, pos] of Object.entries(positions)) {
      const comp = canvasComponents.find((c) => c.id === id);
      if (!comp) continue;
      const delta = { x: pos.x - comp.x, y: pos.y - comp.y };
      await updateComponentPosition(id, delta);
    }
  };

  // Auto route edges on the current layer
  const onAutoRoute = async () => {
    const layerMap: Record<string, string> = {
      'Single-Line Diagram': 'single_line',
      'High-Level Overview': 'high_level',
      'Civil/Structural': 'civil',
      'Networking/Monitoring': 'networking',
      'ODL Code': 'physical',
    };
    const layerName = layerMap[currentLayer] || 'single_line';
    try {
      const resp = await fetch(
        `/api/v1/layout/route?session_id=${sessionId}&layer=${layerName}`,
        { method: 'POST' },
      );
      if (resp.status === 501) throw new Error('client router');
      if (!resp.ok) throw new Error(await resp.text());
      return;
    } catch {
      const lockedLinks: Record<string, boolean> = {};
      links.forEach(
        (e) => (lockedLinks[e.id] = e.locked_in_layers?.[layerName] ?? false),
      );
      const nodes = canvasComponents.map((c) => ({
        id: c.id,
        width: 120,
        height: 72,
        layout: { [layerName]: { x: c.x, y: c.y } },
      }));
      const edges = links.map((l) => ({
        id: l.id,
        source: l.source_id,
        target: l.target_id,
      }));
      const paths = await routeEdgesElk(nodes, edges, layerName as any, lockedLinks);
      await Promise.all(
        Object.entries(paths).map(([id, pts]) =>
          fetch(`/api/v1/links/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              path_by_layer: { [layerName]: pts },
              locked_in_layers: { [layerName]: false },
            }),
          }),
        ),
      );
    }
  };



  // Render ODL Code View for the ODL Code layer
  const renderLayerContent = () => {
    if (currentLayer === 'ODL Code') {
      return (
        // Render ODL code for the active design session
        <ODLCodeView sessionId={sessionId} />
      );
    }

    // Default canvas for other layers
    return (
      <>
        <LinkLayer pendingLink={pendingLink} mousePos={mousePos} />
        <CanvasArea
          pendingLinkSourceId={pendingLink?.sourceId ?? null}
          onStartLink={handleStartLink}
          onEndLink={handleEndLink}
        />
      </>
    );
  };

  return (
    <div
      className="flex-grow h-full relative flex flex-col"
      onMouseMove={handleCanvasMouseMove}
      onMouseUp={handleCanvasMouseUp}
    >
      {/* Display the layer selector and sub-assembly button */}
      <div className="p-2 flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-2">
        <LayerSelector />
        <SubAssemblyButton />
        <button
          onClick={onAutoLayout}
          className="px-3 py-1 rounded-md text-sm bg-gray-100 text-gray-700 hover:bg-gray-200"
        >
          Auto Layout
        </button>
        <button
          onClick={onAutoRoute}
          className="px-3 py-1 rounded-md text-sm bg-gray-100 text-gray-700 hover:bg-gray-200"
        >
          Auto Route
        </button>
      </div>
      <div className="flex-grow relative">
        {renderLayerContent()}
      </div>
    </div>
  );
};

export default Workspace;
