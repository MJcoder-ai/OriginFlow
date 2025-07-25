/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React, { useEffect } from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { useAppStore, UploadEntry } from './appStore';
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import { parseDatasheet } from './services/fileApi';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const {
    bomItems,
    setBom,
    loadUploads,
    addComponent,
    updateComponentPosition,
    updateUpload,
    setActiveDatasheet,
    setRoute,
  } = useAppStore();
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

    // Drop from library onto the canvas to trigger parsing
    if (over.id === 'component-canvas-area' && active.data.current?.type === 'file-asset') {
      const asset = active.data.current.asset as UploadEntry;
      updateUpload(asset.id, { parsing_status: 'processing' });
      setRoute('components');

      parseDatasheet(asset.id)
        .then((parsed) => {
          updateUpload(asset.id, { parsing_status: 'success' });
          setActiveDatasheet({ id: parsed.id, url: parsed.url, payload: parsed.parsed_payload });
        })
        .catch((err) => {
          updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message });
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
