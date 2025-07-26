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
    addStatusMessage,
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
      // If already parsed, load the existing payload and skip re-parsing
      if (asset.parsing_status === 'success') {
        setRoute('components');
        (async () => {
          try {
            const updatedAsset = await getFileStatus(asset.id);
            const fileUrl = `${API_BASE_URL}/files/${updatedAsset.id}/file`;
            setActiveDatasheet({ id: updatedAsset.id, url: fileUrl, payload: updatedAsset.parsed_payload });
          } catch (err: any) {
            console.error('Failed to load parsed datasheet:', err);
            updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
            addStatusMessage('Failed to load datasheet', 'error');
          }
        })();
        return;
      }
      // Otherwise, run the parsing pipeline
      updateUpload(asset.id, { parsing_status: 'processing' });
      setRoute('components');
      // Inform the user that parsing has started
      addStatusMessage('Parsing datasheet...', 'info');

      parseDatasheet(asset.id).catch((err) => {
        updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message });
        addStatusMessage('Datasheet parsing failed', 'error');
      });

      const poll = setInterval(async () => {
        try {
          const updatedAsset = await getFileStatus(asset.id);
          if (updatedAsset.parsing_status === 'success') {
            clearInterval(poll);
            updateUpload(asset.id, { parsing_status: 'success', parsing_error: null });
            const fileUrl = `${API_BASE_URL}/files/${updatedAsset.id}/file`;
            setActiveDatasheet({ id: updatedAsset.id, url: fileUrl, payload: updatedAsset.parsed_payload });
            addStatusMessage('Datasheet parsed successfully', 'success');
          } else if (updatedAsset.parsing_status === 'failed') {
            clearInterval(poll);
            updateUpload(asset.id, { parsing_status: 'failed', parsing_error: updatedAsset.parsing_error });
            addStatusMessage('Datasheet parsing failed', 'error');
          }
        } catch (err: any) {
          clearInterval(poll);
          updateUpload(asset.id, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
          addStatusMessage('Datasheet parsing failed', 'error');
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
