import React, { useCallback } from 'react';
import { useAppStore } from '../appStore';
import { DatasheetSplitView } from './DatasheetSplitView';
import { API_BASE_URL } from '../config';
import { useDroppable } from '@dnd-kit/core';
import { uploadFile, parseDatasheet, updateParsedData, getFileStatus } from '../services/fileApi';

const ComponentCanvas: React.FC = () => {
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const { addUpload, updateUpload, setRoute } = useAppStore();
  const { setNodeRef } = useDroppable({ id: 'component-canvas-area' });

  const handleNativeDrop = useCallback(
    async (file: File) => {
      const tempId = `temp-${Date.now()}`;
      addUpload({
        id: tempId,
        name: file.name,
        size: file.size,
        mime: file.type,
        progress: 0,
        assetType: 'component',
        parsed_at: null,
        parsing_status: null,
        parsing_error: null,
        is_human_verified: false,
      });

      try {
        const uploaded = await uploadFile(file, (p) => updateUpload(tempId, { progress: p }));

        updateUpload(uploaded.id, { ...uploaded, parsing_status: 'processing' });
        setRoute('components');

        await parseDatasheet(uploaded.id);

        const poll = setInterval(async () => {
          const updated = await getFileStatus(uploaded.id);
          if (updated.parsing_status === 'success') {
            clearInterval(poll);
            updateUpload(uploaded.id, { parsing_status: 'success' });
            setActiveDatasheet({ id: updated.id, url: updated.url, payload: updated.parsed_payload });
          } else if (updated.parsing_status === 'failed') {
            clearInterval(poll);
            updateUpload(uploaded.id, { parsing_status: 'failed', parsing_error: updated.parsing_error });
          }
        }, 2000);
      } catch (err: any) {
        console.error(err);
        updateUpload(tempId, { parsing_status: 'failed', parsing_error: 'Upload or parse failed' });
      }
    },
    [addUpload, updateUpload, setActiveDatasheet, setRoute],
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        const file = e.dataTransfer.files[0];
        if (file.type === 'application/pdf') {
          void handleNativeDrop(file);
        }
      }
    },
    [handleNativeDrop],
  );

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => e.preventDefault();

  return (
    <div ref={setNodeRef} className="w-full h-full flex flex-col" onDrop={onDrop} onDragOver={onDragOver}>
      {activeDatasheet ? (
        <DatasheetSplitView
          pdfUrl={`${API_BASE_URL}${activeDatasheet.url}`}
          parsedData={activeDatasheet.payload}
          onSave={(payload) => {
            updateParsedData(activeDatasheet.id, payload).then((updated) => {
              setActiveDatasheet({ id: updated.id, url: updated.url, payload: updated.parsed_payload });
            });
          }}
          onClose={() => setActiveDatasheet(null)}
        />
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400 border-2 border-dashed rounded-lg pointer-events-none">
          <p>Drop a component from the library or a PDF from your computer to begin.</p>
        </div>
      )}
    </div>
  );
};

export default ComponentCanvas;
