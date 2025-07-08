/**
 * File: frontend/src/components/StatusBar.tsx
 * Bottom status bar providing workspace metadata and indicators.
 * Shows placeholder status information currently.
 */
import React from 'react';
import { useAppStore } from '../appStore';

/** Persistent bottom status bar. */
const StatusBar: React.FC = () => {
  const status = useAppStore((state) => state.status);

  return (
    <footer className="[grid-area:statusbar] bg-white border-t border-gray-200 px-4 flex items-center h-10 text-sm">
      <span className="text-gray-600 capitalize">Status: {status}</span>
    </footer>
  );
};

export default StatusBar;
