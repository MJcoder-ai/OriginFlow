/**
 * File: frontend/src/components/StatusBar.tsx
 * Bottom status bar providing workspace metadata and indicators.
 * Shows placeholder status information currently.
 */
import React from 'react';

/** Persistent bottom status bar. */
const StatusBar: React.FC = () => (
  <footer className="[grid-area:statusbar] bg-white border-t border-gray-200 px-4 flex items-center h-10 text-sm">
    <span className="text-gray-600">Status: Ready</span>
  </footer>
);

export default StatusBar;
