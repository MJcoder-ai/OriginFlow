import { useAppStore, UploadEntry } from '../appStore';
import clsx from 'clsx';
import { useDraggable } from '@dnd-kit/core';

const FileEntry: React.FC<{ u: UploadEntry }> = ({ u }) => {
  const { attributes, listeners, setNodeRef } = useDraggable({
    id: `file-asset-${u.id}`,
    data: { type: 'file-asset', asset: u },
  });
  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={clsx(
        'border rounded p-2 text-sm transition cursor-grab',
        u.progress >= 200 && 'opacity-50',
      )}
    >
      <div className="font-medium truncate">{u.name}</div>
      <div className="h-1 bg-gray-200 rounded">
        <div
          className={clsx(
            'h-1 rounded bg-emerald-500 transition-all',
            u.progress > 100 ? 'w-full' : undefined,
          )}
          style={{ width: `${Math.min(u.progress, 100)}%` }}
        />
      </div>
      <div className="text-xs text-right">
        {u.progress > 100 ? 'Waiting for AI' : `${u.progress}%`}
      </div>
    </div>
  );
};

export const FileStagingArea = () => {
  const uploads = useAppStore((s) => s.uploads.filter((u) => u.assetType === 'component'));
  if (!uploads.length) return null;

  return (
    <div className="absolute bottom-2 left-2 w-56 space-y-2 z-20">
      {uploads.map((u) => (
        <FileEntry key={u.id} u={u} />
      ))}
    </div>
  );
};
