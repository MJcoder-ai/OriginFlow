/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React, { useEffect } from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { useAppStore } from './appStore';
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const { bomItems, setBom, loadUploads, addComponent, updateComponentPosition } = useAppStore();
  const sensors = useSensors(useSensor(PointerSensor));

  const handleDragEnd = (event: any) => {
    const { active, over, delta } = event;
    if (!over) return;

    if (over.id === 'canvas-area' && active.data.current?.type === 'file-asset') {
      const asset = active.data.current.asset;
      addComponent({
        name: asset.name,
        type: asset.mime,
        standard_code: asset.id,
      });
      return;
    }

    if (active.data.current?.type === 'canvas-card') {
      updateComponentPosition(active.id, { x: delta.x, y: delta.y });
    }
  };

  useEffect(() => {
    loadUploads();
  }, [loadUploads]);


  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      {/* Ensure the app container fills the height so the grid stretches */}
      <div className="App h-full">
        <Layout />
        {bomItems && <BomModal items={bomItems} onClose={() => setBom(null)} />}
      </div>
    </DndContext>
  );
};

export default App;
