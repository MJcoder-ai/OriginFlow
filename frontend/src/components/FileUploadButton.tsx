import { Paperclip } from 'lucide-react';
import { presign, complete, uploadWithProgress } from '../services/fileApi';
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

    const { upload_url, asset_id } = await presign(file.name, file.type);

    addUpload({
      id: asset_id,
      name: file.name,
      size: file.size,
      mime: file.type,
      progress: 0,
    });

    await uploadWithProgress(upload_url, file, (p) =>
      updateUpload(asset_id, { progress: p }),
    );

    await complete({
      asset_id,
      filename: file.name,
      mime: file.type,
      size: file.size,
      component_id: null,
    });

    updateUpload(asset_id, { progress: 101 });

    useAppStore.getState().addMessage({
      id: generateId('msg'),
      author: 'AI',
      text: `✅ Uploaded *${file.name}* (${prettyBytes(file.size)}) – parsing…`,
    });
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
