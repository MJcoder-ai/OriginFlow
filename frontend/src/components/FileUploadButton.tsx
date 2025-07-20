import { Paperclip } from 'lucide-react';
import { uploadFile } from '../services/fileApi';
import { useAppStore } from '../appStore';
import prettyBytes from 'pretty-bytes';
import { generateId } from '../utils/id';
import { useRef } from 'react';

export const FileUploadButton = () => {
  const inputRef = useRef<HTMLInputElement>(null);
  const { addUpload, updateUpload } = useAppStore();

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

    try {
      const asset = await uploadFile(file, (p) => updateUpload(tempId, { progress: p }));
      updateUpload(tempId, {
        id: asset.id,
        progress: 101,
        parsing_status: asset.parsing_status ?? null,
        parsing_error: asset.parsing_error ?? null,
        is_human_verified: asset.is_human_verified ?? false,
      });
      useAppStore
        .getState()
        .addMessage({ id: generateId('msg'), author: 'AI', text: `✅ Uploaded *${file.name}* (${prettyBytes(file.size)}) – parsing…` });
    } catch (error) {
      console.error('Upload failed', error);
      updateUpload(tempId, { progress: -1 });
      useAppStore.getState().addMessage({ id: generateId('msg'), author: 'AI', text: `❌ Upload failed for *${file.name}*` });
    }
  };

  return (
    <>
      <input type="file" ref={inputRef} onChange={onSelect} className="hidden" />
      <button onClick={choose} className="p-2 text-gray-500 hover:text-blue-600 transition-colors">
        <Paperclip size={20} />
      </button>
    </>
  );
};
