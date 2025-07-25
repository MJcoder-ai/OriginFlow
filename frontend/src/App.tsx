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
import { parseDatasheet, getFileStatus } from './services/fileApi';
import { API_BASE_URL } from './config';

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

    // Drop from library onto the component canvas to trigger parsing
    if (over.id === 'component-canvas-area' && active.data.current?.type === 'file-asset') {
      const asset = active.data.current.asset as UploadEntry;
      // Immediately mark the upload as processing and switch the view
      updateUpload(asset.id, { parsing_status: 'processing' });
      setRoute('components');

      // Kick off the parsing job (runs async on the backend)
      parseDatasheet(asset.id).catch((err) => {
        updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message });
      });

      // Poll for status until completed
      const poll = setInterval(async () => {
        try {
          const updatedAsset = await getFileStatus(asset.id);
          if (updatedAsset.parsing_status === 'success') {
            clearInterval(poll);
            updateUpload(asset.id, { parsing_status: 'success', parsing_error: null });
            const fileUrl = `${API_BASE_URL}/files/${updatedAsset.id}/file`;
            setActiveDatasheet({ id: updatedAsset.id, url: fileUrl, payload: updatedAsset.parsed_payload });
          } else if (updatedAsset.parsing_status === 'failed') {
            clearInterval(poll);
            updateUpload(asset.id, { parsing_status: 'failed', parsing_error: updatedAsset.parsing_error });
          }
        } catch (err: any) {
          clearInterval(poll);
          updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
        }
      }, 2000);

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
