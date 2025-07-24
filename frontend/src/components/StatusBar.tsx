import React from 'react';
import { useAppStore } from '../appStore';

const statusColors: Record<string, string> = {
  info: 'text-blue-600',
  success: 'text-green-600',
  error: 'text-red-600',
};

const StatusBar: React.FC = () => {
  const messages = useAppStore((s) => s.statusMessages);
  const latest = messages[messages.length - 1];
  const colorClass = latest?.icon ? statusColors[latest.icon] ?? 'text-gray-600' : 'text-gray-600';

  return (
    <footer
      role="status"
      aria-live="polite"
      className={`grid-in-status flex items-center px-4 py-2 bg-white text-black border-t border-gray-200 text-sm ${colorClass}`}
    >
      {latest?.message ?? 'Ready'}
    </footer>
  );
};

export default StatusBar;
