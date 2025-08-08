import React, { useCallback } from 'react';
import { useAppStore } from '../appStore';
import { DatasheetSplitView } from './DatasheetSplitView';
import { useDroppable } from '@dnd-kit/core';
import { uploadFile, parseDatasheet, getFileStatus } from '../services/fileApi';
import { API_BASE_URL } from '../config';

const ComponentCanvas: React.FC = () => {
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const { addUpload, updateUpload, setRoute, addStatusMessage } = useAppStore();
  const { setNodeRef } = useDroppable({ id: 'component-canvas-area' });

  const handleNativeDrop = useCallback(
    async (file: File) => {
      // Add a temporary upload entry while uploading
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
        // Upload the file and track progress
        const uploaded = await uploadFile(file, (p) => updateUpload(tempId, { progress: p }));
        // Replace the temp entry with the real asset and mark processing
        updateUpload(uploaded.id, { ...uploaded, parsing_status: 'processing' });
        // Show the components view
        setRoute('components');

        // Trigger parsing asynchronously
        parseDatasheet(uploaded.id).catch((err) => {
          updateUpload(uploaded.id, { parsing_status: 'failed', parsing_error: err.message });
        });

        // Poll backend until parsing finishes
        const poll = setInterval(async () => {
          try {
            const updated = await getFileStatus(uploaded.id);
            if (updated.parsing_status === 'success') {
              clearInterval(poll);
              updateUpload(uploaded.id, { parsing_status: 'success', parsing_error: null });
              const fileUrl = `${API_BASE_URL}/files/${updated.id}/file`;
              setActiveDatasheet({ id: updated.id, url: fileUrl, payload: updated.parsed_payload });
            } else if (updated.parsing_status === 'failed') {
              clearInterval(poll);
              updateUpload(uploaded.id, { parsing_status: 'failed', parsing_error: updated.parsing_error });
            }
          } catch (err: any) {
            clearInterval(poll);
            updateUpload(uploaded.id, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
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

  const handleClose = () => setActiveDatasheet(null);

  return (
    <div ref={setNodeRef} className="w-full h-full flex flex-col" onDrop={onDrop} onDragOver={onDragOver}>
      {activeDatasheet ? (
        <DatasheetSplitView
          assetId={activeDatasheet.id}
          pdfUrl={activeDatasheet.url}
          onClose={handleClose}
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
