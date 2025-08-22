import { Paperclip, Loader2 } from 'lucide-react';
import { uploadFile } from '../services/fileApi';
import { useAppStore } from '../appStore';
// pretty-bytes is not used here
import { generateId } from '../utils/id';
import { useRef } from 'react';

export const FileUploadButton = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const { addUpload, updateUpload, addMessage, addStatusMessage, uploads } = useAppStore();

  const choose = () => inputRef.current?.click();

  const onSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

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

    // Inform the user that the upload has started
    addStatusMessage(`Uploading ${file.name}…`, 'info');

    try {
      const asset = await uploadFile(file, (p) => updateUpload(tempId, { progress: p }));
      // Replace the temp entry with the real one but leave parsing_status null (unparsed)
      updateUpload(tempId, {
        ...asset,
        id: asset.id,
        progress: 101,
        parsing_status: null,
        parsing_error: null,
      });
      // Capitalised author to conform to Message type
      addMessage({ id: crypto.randomUUID(), author: 'User', text: `Uploaded ${file.name}` });
      addStatusMessage('Upload complete', 'success');
    } catch (error: any) {
      console.error('Upload failed', error);
      updateUpload(tempId, { progress: -1 });
      // Use capitalised author to match the Message type
      addMessage({ id: crypto.randomUUID(), author: 'User', text: `❌ Upload failed for ${file.name}` });
      if (error?.status === 401) {
        addStatusMessage('Unauthorized. Please log in to upload files.', 'error');
      } else {
        addStatusMessage('Upload failed', 'error');
      }
    }
  };

  return (
    <>
      <input type="file" ref={inputRef} onChange={onSelect} className="hidden" />
      <button
        onClick={choose}
        className="relative p-2 text-gray-500 hover:text-blue-600 transition-colors"
        aria-label="Upload file"
      >
        {/* Base paperclip icon */}
        <Paperclip size={20} />
        {/* Spinner shows when any uploads are in progress */}
        {uploads.some((u) => u.progress >= 0 && u.progress < 100) && (
          <Loader2 size={14} className="absolute top-0 right-0 text-blue-600 animate-spin" />
        )}
        {/* Badge displays the count of active uploads */}
        {(() => {
          const count = uploads.filter((u) => u.progress >= 0 && u.progress < 100).length;
          return count > 0 ? (
            <span
              className="absolute -top-1 -right-1 bg-red-600 text-white rounded-full text-xs w-4 h-4 flex items-center justify-center"
            >
              {count}
            </span>
          ) : null;
        })()}
      </button>
    </>
  );
};
