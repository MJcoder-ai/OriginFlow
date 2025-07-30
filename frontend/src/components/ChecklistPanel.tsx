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

  const components = useAppStore((s) => s.canvasComponents);
  const renderAction = (action: AiAction) => {
    switch (action.action) {
      case 'addComponent': {
        return `Add ${action.payload.type} “${action.payload.name}”`;
      }
      case 'removeComponent': {
        const comp = components.find((c) => c.id === action.payload.id);
        const name = comp ? comp.name : action.payload.id;
        return `Remove ${name}`;
      }
      case 'addLink': {
        const source = components.find((c) => c.id === action.payload.source_id);
        const target = components.find((c) => c.id === action.payload.target_id);
        const srcName = source ? source.name : action.payload.source_id;
        const tgtName = target ? target.name : action.payload.target_id;
        return `Connect ${srcName} to ${tgtName}`;
      }
      case 'updatePosition': {
        const comp = components.find((c) => c.id === action.payload.id);
        const name = comp ? comp.name : action.payload.id;
        return `Move ${name} to (${action.payload.x}, ${action.payload.y})`;
      }
      case 'report': {
        return 'Show bill of materials';
      }
      case 'validation': {
        return action.payload.message || 'Validation message';
      }
      default: {
        return JSON.stringify(action);
      }
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
