/**
 * File: frontend/src/components/StatusBar.tsx
 * Bottom status bar providing workspace metadata and indicators.
 * Shows placeholder status information currently.
 */
import React, { useEffect } from 'react';
import { useAppStore } from '../appStore';

/** Persistent bottom status bar. */
const StatusBar: React.FC = () => {
  const statuses = useAppStore((s) => s.statusMessages);
  const removeStatus = useAppStore((s) => s.removeStatusMessage);

  useEffect(() => {
    if (statuses.length > 0) {
      const timeout = setTimeout(() => {
        removeStatus(statuses[0].id);
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [statuses, removeStatus]);

  if (statuses.length === 0) return null;

  return (
    <div
      className="w-full h-[48px] flex items-center gap-4 px-4 bg-gray-800 text-white text-sm shadow-inner"
      role="status"
      aria-live="polite"
    >
      {statuses.map((status) => (
        <div key={status.id} className="flex items-center gap-2">
          {status.icon && <span>{status.icon}</span>}
          <span>{status.message}</span>
        </div>
      ))}
    </div>
  );
};

export default StatusBar;
