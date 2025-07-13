import { useAppStore } from '../appStore';
import clsx from 'clsx';

export const FileStagingArea = () => {
  const uploads = useAppStore((s) => s.uploads);
  if (!uploads.length) return null;

  return (
    <div className="absolute right-2 top-2 w-56 space-y-2 z-20">
      {uploads.map((u) => (
        <div
          key={u.id}
          className={clsx(
            'border rounded p-2 text-sm transition',
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
      ))}
    </div>
  );
};
