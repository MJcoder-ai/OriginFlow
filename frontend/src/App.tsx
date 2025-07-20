/**
 * File: frontend/src/App.tsx
 * Root component for the OriginFlow React application.
 * Renders the main layout container.
 */
import React, { useEffect } from 'react';
import Layout from './components/Layout';
import { BomModal } from './components/BomModal';
import { DatasheetSplitView } from './components/DatasheetSplitView';
import { useAppStore } from './appStore';
import { updateParsedData } from './services/fileApi';

/** Main application component wrapping the Layout. */
const App: React.FC = () => {
  const {
    bomItems,
    setBom,
    loadUploads,
    activeDatasheet,
    setActiveDatasheet,
    updateUpload,
  } = useAppStore();

  useEffect(() => {
    loadUploads();
  }, [loadUploads]);

  const handleSave = async (id: string, payload: any) => {
    try {
      const updated = await updateParsedData(id, payload);
      setActiveDatasheet({ id: updated.id, url: updated.url, payload: updated.parsed_payload });
      updateUpload(id, {
        parsed_at: updated.parsed_at,
        is_human_verified: true,
      });
    } catch (error) {
      console.error('Failed to save datasheet', error);
    }
  };

  return (
    <div className="App">
      <Layout />
      {bomItems && <BomModal items={bomItems} onClose={() => setBom(null)} />}

      {activeDatasheet && (
        <DatasheetSplitView
          assetId={activeDatasheet.id}
          pdfUrl={activeDatasheet.url}
          initialParsedData={activeDatasheet.payload}
          onClose={() => setActiveDatasheet(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
};

export default App;
