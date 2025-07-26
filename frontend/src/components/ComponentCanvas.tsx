import React, { useCallback, useRef } from 'react';
import { useAppStore } from '../appStore';
import { DatasheetSplitView } from './DatasheetSplitView';
import { useDroppable } from '@dnd-kit/core';
import {
  uploadFile,
  parseDatasheet,
  updateParsedData,
  getFileStatus,
} from '../services/fileApi';
import { API_BASE_URL } from '../config';

const ComponentCanvas: React.FC = () => {
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const { addUpload, updateUpload, setRoute, addStatusMessage } = useAppStore();
  const { setNodeRef } = useDroppable({ id: 'component-canvas-area' });
  const analyzeIntervalRef = useRef<NodeJS.Timeout | null>(null);

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

  // Save edits back to the backend (PATCH /files/{id}) and update the view
  // Save edits back to the backend (PATCH /files/{id}).  When isHumanVerified is false,
  // the datasheet remains in an unconfirmed state.  On success, reload the
  // updated asset and show a toast message.
  const handleSave = (assetId: string, updatedData: any) => {
    updateParsedData(assetId, updatedData, false)
      .then((updated) => {
        const fileUrl = `${API_BASE_URL}/files/${updated.id}/file`;
        setActiveDatasheet({ id: updated.id, url: fileUrl, payload: updated.parsed_payload });
        addStatusMessage('Changes saved', 'success');
      })
      .catch((err) => {
        console.error('Failed to save datasheet', err);
        addStatusMessage('Failed to save datasheet', 'error');
      });
  };

  // Confirm edits and close the editor.  Persist the updated data and
  // mark the datasheet as human verified.  On success, reload the asset
  // and show a toast message.
  const handleConfirm = (assetId: string, updatedData: any) => {
    updateParsedData(assetId, updatedData, true)
      .then((updated) => {
        const fileUrl = `${API_BASE_URL}/files/${updated.id}/file`;
        setActiveDatasheet({ id: updated.id, url: fileUrl, payload: updated.parsed_payload });
        addStatusMessage('Datasheet confirmed', 'success');
      })
      .catch((err) => {
        console.error('Failed to confirm datasheet', err);
        addStatusMessage('Failed to confirm datasheet', 'error');
      });
  };

  // Trigger a fresh parse and poll until complete (for “Re-Analyze”)
  const handleAnalyze = (assetId: string) => {
    if (analyzeIntervalRef.current) return;
    addStatusMessage('Re-analyzing datasheet...', 'info');
    parseDatasheet(assetId).catch((err) => {
      console.error('Re-Analyze failed', err);
      addStatusMessage('Re-Analyze failed', 'error');
      if (analyzeIntervalRef.current) {
        clearInterval(analyzeIntervalRef.current);
        analyzeIntervalRef.current = null;
      }
    });
    analyzeIntervalRef.current = setInterval(async () => {
      try {
        const updated = await getFileStatus(assetId);
        if (updated.parsing_status === 'success') {
          clearInterval(analyzeIntervalRef.current!);
          analyzeIntervalRef.current = null;
          updateUpload(assetId, { parsing_status: 'success', parsing_error: null });
          const fileUrl = `${API_BASE_URL}/files/${updated.id}/file`;
          setActiveDatasheet({ id: updated.id, url: fileUrl, payload: updated.parsed_payload });
          addStatusMessage('Datasheet parsed successfully', 'success');
        } else if (updated.parsing_status === 'failed') {
          clearInterval(analyzeIntervalRef.current!);
          analyzeIntervalRef.current = null;
          updateUpload(assetId, { parsing_status: 'failed', parsing_error: updated.parsing_error });
          addStatusMessage('Datasheet parsing failed', 'error');
        }
      } catch (err: any) {
        clearInterval(analyzeIntervalRef.current!);
        analyzeIntervalRef.current = null;
        updateUpload(assetId, { parsing_status: 'failed', parsing_error: err.message || 'Failed to fetch status' });
        addStatusMessage('Datasheet parsing failed', 'error');
      }
    }, 2000);
  };

  const handleClose = () => setActiveDatasheet(null);

  return (
    <div ref={setNodeRef} className="w-full h-full flex flex-col" onDrop={onDrop} onDragOver={onDragOver}>
      {activeDatasheet ? (
        <DatasheetSplitView
          assetId={activeDatasheet.id}
          pdfUrl={activeDatasheet.url}
          initialParsedData={activeDatasheet.payload}
          onSave={handleSave}
          onConfirm={handleConfirm}
          onAnalyze={handleAnalyze}
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
