/**
 * File: frontend/src/components/QuickActionBar.tsx
 * Displays a horizontal list of quick action buttons below the chat
 * history and above the chat input.  Quick actions are populated by
 * the orchestrator to surface commonly used commands or next steps.
 */
import React from 'react';
import { useAppStore } from '../appStore';

const QuickActionBar: React.FC = () => {
  const quickActions = useAppStore((s) => s.quickActions);
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  if (!quickActions || quickActions.length === 0) return null;
  return (
    <div className="grid-in-chat-actions border-t border-gray-200 bg-white px-3 py-2 flex flex-wrap gap-2">
      {quickActions.map((action) => (
        <button
          key={action.id}
          onClick={() => analyzeAndExecute(action.command)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-3 py-1 rounded-md transition-colors"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
};

export default QuickActionBar;

