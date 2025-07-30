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
  const costTotal = useAppStore((s) => s.costTotal);
  const pendingCount = useAppStore((s) => s.pendingActions.length);
  const colorClass = latest?.icon ? statusColors[latest.icon] ?? 'text-gray-600' : 'text-gray-600';

  return (
    <footer
      role="status"
      aria-live="polite"
      className={`grid-in-status flex items-center justify-between px-4 py-2 bg-white text-black border-t border-gray-200 text-sm ${colorClass}`}
    >
      {/* Left segment: status message */}
      <div className="flex-1 truncate">
        {latest?.message ?? 'Ready'}
      </div>
      {/* Middle segment: cost total */}
      <div className="flex-1 text-right pr-4">
        {costTotal > 0 ? `Cost: $${costTotal.toFixed(2)}` : ''}
      </div>
      {/* Right segment: pending actions count */}
      <div className="flex-1 text-right">
        {pendingCount > 0 ? `${pendingCount} pending` : ''}
      </div>
    </footer>
  );
};

export default StatusBar;
