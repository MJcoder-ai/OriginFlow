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
      className={`h-12 flex items-center px-6 bg-white border-t shadow text-sm ${colorClass}`}
    >
      {latest?.message ?? 'Ready'}
    </footer>
  );
};

export default StatusBar;
