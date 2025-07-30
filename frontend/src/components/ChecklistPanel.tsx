import React from 'react';
import { useAppStore } from '../appStore';
import { AiAction } from '../types/ai';

const ChecklistPanel: React.FC = () => {
  const pendingActions = useAppStore((s) => s.pendingActions);
  const approve = useAppStore((s) => s.approvePendingAction);
  const reject = useAppStore((s) => s.rejectPendingAction);

  if (!pendingActions.length) {
    return null;
  }

  const renderAction = (action: AiAction) => {
    switch (action.action) {
      case 'addComponent':
        return `Add component ${action.payload.name} (${action.payload.type})`;
      case 'removeComponent':
        return `Remove component ${action.payload.id}`;
      case 'addLink':
        return `Connect ${action.payload.source_id} to ${action.payload.target_id}`;
      case 'updatePosition':
        return `Move component ${action.payload.id} to (${action.payload.x}, ${action.payload.y})`;
      case 'report':
        return 'Show bill of materials';
      case 'validation':
        return action.payload.message || 'Validation message';
      default:
        return JSON.stringify(action);
    }
  };

  return (
    <div className="p-4 bg-white border border-gray-300 rounded-md shadow-sm mb-4">
      <h3 className="font-semibold mb-2">Pending AI Actions</h3>
      <ul className="space-y-2">
        {pendingActions.map((action, idx) => (
          <li key={idx} className="flex items-center justify-between">
            <span className="text-sm mr-2 flex-1">{renderAction(action)}</span>
            <div className="flex space-x-2">
              <button
                onClick={() => approve(idx)}
                className="px-2 py-1 text-xs rounded-md bg-green-500 text-white hover:bg-green-600"
              >
                Approve
              </button>
              <button
                onClick={() => reject(idx)}
                className="px-2 py-1 text-xs rounded-md bg-red-500 text-white hover:bg-red-600"
              >
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ChecklistPanel;
