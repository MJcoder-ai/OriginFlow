/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace housing the canvas, properties panel, and drag-and-drop logic.
 * Implements panel resizing and component placement on the canvas.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { DndContext, useDroppable, DragEndEvent } from '@dnd-kit/core';
import { useAppStore, CanvasComponent } from '../appStore';
import PropertiesPanel from './PropertiesPanel';

/** A component card rendered on the canvas. */
const CanvasCard: React.FC<{ component: CanvasComponent }> = ({ component }) => (
  <div className="h-24 w-32 bg-white border border-gray-300 rounded-lg shadow-sm flex flex-col items-center justify-center p-2">
    <span className="text-sm font-bold">{component.name}</span>
    <span className="text-xs text-gray-500">{component.type}</span>
  </div>
);

/** The main canvas area that acts as a droppable target. */
const CanvasArea: React.FC = () => {
  const { setNodeRef } = useDroppable({ id: 'canvas-area' });
  const components = useAppStore((state) => state.canvasComponents);

  return (
    <div
      ref={setNodeRef}
      className="flex-grow h-full border-2 border-dashed border-gray-300 rounded-lg p-4 flex flex-wrap gap-4 content-start"
    >
      {components.length > 0 ? (
        components.map((comp) => <CanvasCard key={comp.id} component={comp} />)
      ) : (
        <span className="text-gray-400">Drop components here</span>
      )}
    </div>
  );
};

/** A visual element for resizing the panel */
const Resizer: React.FC<{ onMouseDown: (e: React.MouseEvent) => void }> = ({ onMouseDown }) => (
  <div
    onMouseDown={onMouseDown}
    className="w-1.5 cursor-col-resize bg-gray-200 hover:bg-blue-500 transition-colors"
  ></div>
);

/** Primary workspace container orchestrating drag-and-drop and resizing. */
const Workspace: React.FC = () => {
  const addComponent = useAppStore((state) => state.addComponent);

  // state for resizing the properties panel
  const [isDragging, setIsDragging] = useState(false);
  const [panelWidth, setPanelWidth] = useState(300);

  const handleDragEnd = (event: DragEndEvent) => {
    if (event.over && event.over.id === 'canvas-area') {
      const componentType = event.active.data.current?.type;
      if (componentType) {
        addComponent(componentType);
      }
    }
  };

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (isDragging) {
        const newWidth = window.innerWidth - e.clientX - 80; // account for layout offsets
        if (newWidth > 200 && newWidth < 600) {
          setPanelWidth(newWidth);
        }
      }
    },
    [isDragging]
  );

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
        <CanvasArea />
        <Resizer onMouseDown={handleMouseDown} />
        <div style={{ width: `${panelWidth}px` }} className="min-w-[200px] max-w-[600px]">
          <PropertiesPanel />
        </div>
      </main>
    </DndContext>
  );
};

export default Workspace;
