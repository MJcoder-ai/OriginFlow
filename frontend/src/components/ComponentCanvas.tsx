import React from 'react';
import { useAppStore } from '../appStore';
import { uploadFile, parseDatasheet } from '../services/fileApi';

const ComponentCanvas = () => {
  const { setActiveDatasheet, updateUpload } = useAppStore();

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      try {
        const asset = await uploadFile(file, () => {});
        const parsed = await parseDatasheet(asset.id);
        setActiveDatasheet({ id: parsed.id, url: parsed.url, payload: parsed.parsed_payload });
        updateUpload(parsed.id, { parsed_at: parsed.parsed_at });
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="[grid-area:workspace] flex items-center justify-center text-gray-500 border-2 border-dashed rounded"
    >
      Drag datasheet PDF here
    </div>
  );
};

export default ComponentCanvas;
