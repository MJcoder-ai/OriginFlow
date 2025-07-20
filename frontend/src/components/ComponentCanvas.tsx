import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { useAppStore } from '../appStore';
import { uploadFile, parseDatasheet, getFileStatus } from '../services/fileApi';
import { generateId } from '../utils/id';

/** Canvas used for parsing new components from uploaded datasheets. */
const ComponentCanvas = () => {
  // Register this canvas as a drop target for dnd-kit
  const { setNodeRef } = useDroppable({ id: 'component-canvas' });
  const { addUpload, updateUpload, setActiveDatasheet } = useAppStore();

  const handleFileDrop = async (file: File) => {
    const tempId = generateId('upload');
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
      const asset = await uploadFile(file, (p) => updateUpload(tempId, { progress: p }));
      updateUpload(tempId, {
        id: asset.id,
        progress: 101,
        parsing_status: asset.parsing_status ?? null,
        parsing_error: asset.parsing_error ?? null,
        is_human_verified: asset.is_human_verified ?? false,
      });

      parseDatasheet(asset.id).catch((err) => console.error(err));
      updateUpload(asset.id, { parsing_status: 'processing' });

      const poll = async () => {
        try {
          const status = await getFileStatus(asset.id);
          updateUpload(asset.id, {
            parsing_status: status.parsing_status ?? null,
            parsing_error: status.parsing_error ?? null,
            parsed_at: status.parsed_at,
          });
          if (status.parsing_status === 'success') {
            setActiveDatasheet({ id: status.id, url: status.url, payload: status.parsed_payload });
            return;
          }
          if (status.parsing_status === 'failed') {
            return;
          }
          setTimeout(poll, 2000);
        } catch (e) {
          console.error(e);
        }
      };
      poll();
    } catch (error) {
      console.error('Upload failed', error);
      updateUpload(tempId, { progress: -1 });
    }
  };

  return (
    <div
      ref={setNodeRef}
      className="relative w-full h-full flex items-center justify-center text-gray-500 border-2 border-dashed rounded-lg bg-gray-50"
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && file.type === 'application/pdf') {
          handleFileDrop(file);
        }
      }}
    >
      Drag a datasheet from the library or your desktop here to parse it.
    </div>
  );
};

export default ComponentCanvas;
