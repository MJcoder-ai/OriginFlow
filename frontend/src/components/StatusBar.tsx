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
  const cost = useAppStore((s) => s.costTotal);
  const perf = useAppStore((s) => s.performanceMetrics.annualKwh);

  return (
    <footer
      role="status"
      aria-live="polite"
      className={`grid-in-status flex items-center justify-between px-4 py-2 bg-white text-black border-t border-gray-200 text-sm ${colorClass}`}
    >
      {/* Left section: latest status message */}
      <span className="flex-1 truncate">
        {latest?.message ?? 'Ready'}
      </span>
      {/* Middle section: cost and performance */}
      <span className="flex-none ml-4 whitespace-nowrap">
        {cost !== null && <span className="mr-4">Cost: ${cost.toFixed(0)}</span>}
        {perf !== null && <span>Annual kWh: {perf.toLocaleString()}</span>}
      </span>
      {/* Right section removed (pending actions no longer exist) */}
    </footer>
  );
};

export default StatusBar;
