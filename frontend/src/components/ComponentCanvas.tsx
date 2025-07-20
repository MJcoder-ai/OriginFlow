import React, { useState } from 'react';
import { useDroppable } from '@dnd-kit/core';
import DatasheetSplitView from './DatasheetSplitView';

const ComponentCanvas: React.FC = () => {
  const { setNodeRef } = useDroppable({ id: 'component-canvas' });
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [parsedData, setParsedData] = useState<any | null>(null);
  const [assetId, setAssetId] = useState<string | null>(null);

  const handleDrop = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/v1/parse-datasheet', { method: 'POST', body: formData });
    const result = await res.json();
    const blobUrl = URL.createObjectURL(file);
    setPdfUrl(blobUrl);
    setParsedData(result.fields);
    setAssetId(result.assetId || file.name);
  };

  return (
    <div
      ref={setNodeRef}
      className="w-full h-full bg-white border border-gray-200 rounded-md flex overflow-hidden"
      onDrop={(e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file?.type === 'application/pdf') handleDrop(file);
      }}
      onDragOver={(e) => e.preventDefault()}
    >
      {!pdfUrl && (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          Drag a datasheet from the library or your desktop here to parse it.
        </div>
      )}
      {pdfUrl && parsedData && assetId && (
        <DatasheetSplitView
          assetId={assetId}
          pdfUrl={pdfUrl}
          initialParsedData={parsedData}
          onClose={() => {
            setPdfUrl(null);
            setParsedData(null);
          }}
          onSave={(id, payload) => {
            fetch(`/api/v1/components/${id}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
            });
          }}
        />
      )}
    </div>
  );
};

export default ComponentCanvas;
