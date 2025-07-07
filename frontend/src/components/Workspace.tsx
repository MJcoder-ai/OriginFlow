/**
 * File: frontend/src/components/Workspace.tsx
 * Central workspace housing the canvas, properties panel, and their interaction logic.
 * Implements component placement and selection highlighting.
 * Handles component selection and highlights the active element.
*/
import React from 'react';
import {
  DndContext,
  useDroppable,
  useDraggable,
  DragEndEvent,
} from '@dnd-kit/core';
import { useAppStore, CanvasComponent } from '../appStore';
import PropertiesPanel from './PropertiesPanel';
import LinkLayer from './LinkLayer';
import clsx from 'clsx';

/** A component card rendered on the canvas with a connection handle */
const CanvasCard: React.FC<{ component: CanvasComponent }> = ({ component }) => {
  const { selectedComponentId, selectComponent } = useAppStore();
  const isSelected = selectedComponentId === component.id;

  // Enable dragging of the card itself
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: component.id,
  });

  // Apply drag transform if available, otherwise use stored position
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : { top: component.y, left: component.x };

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
      <div className="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-red-400 rounded-full border-2 border-white cursor-crosshair"></div>
    </div>
  );
};

/** The main canvas area that is a droppable target */
const CanvasArea: React.FC = () => {
  const { setNodeRef } = useDroppable({ id: 'canvas-area' });
  const components = useAppStore((state) => state.canvasComponents);
  const selectComponent = useAppStore((state) => state.selectComponent);

  return (
    <div className="flex-grow h-full relative" onClick={() => selectComponent(null)}>
      <LinkLayer />
      <div
        ref={setNodeRef}
        className="w-full h-full border-2 border-dashed border-gray-300 rounded-lg relative"
      >
        {components.length > 0 ? (
          components.map((comp) => <CanvasCard key={comp.id} component={comp} />)
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-gray-400">Drop components here</span>
          </div>
        )}
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
  const { addComponent, updateComponentPosition } = useAppStore();

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



  return (
    <DndContext onDragEnd={handleDragEnd}>
      <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
        <CanvasArea />
        <Resizer />
        <div className="w-[300px]">
          <PropertiesPanel />
        </div>
      </main>
    </DndContext>
  );
};

export default Workspace;
