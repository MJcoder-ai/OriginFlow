import { useAppStore, UploadEntry } from '../appStore';
import clsx from 'clsx';
import { useDraggable } from '@dnd-kit/core';

const FileEntry: React.FC<{ u: UploadEntry }> = ({ u }) => {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `file-asset-${u.id}`,
    data: { type: 'file-asset', asset: u },
  });
  return (
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={clsx(
        'border rounded p-2 text-sm transition cursor-grab bg-white shadow-sm',
        isDragging && 'opacity-50',
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
      <div className="text-xs text-right text-gray-500">
        {u.progress > 100 ? 'Ready to use' : `${u.progress}%`}
      </div>
    </div>
  );
};

export const FileStagingArea = () => {
  const uploads = useAppStore((s) => s.uploads.filter((u) => u.progress > 100));
  if (!uploads.length) return null;

  return (
    <div className="p-2 space-y-2">
      <div className="text-sm font-medium text-gray-500 px-2">Component Library</div>
      {uploads.map((u) => (
        <FileEntry key={u.id} u={u} />
      ))}
    </div>
  );
};
