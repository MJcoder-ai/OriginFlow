/**
 * File: frontend/src/components/DesignCard.tsx
 * Renders a structured card message within the chat history.  Cards are
 * used by the AI to present component suggestions, bill of materials
 * summaries and other rich data to the user.  Each card can include
 * an image, a specs table and a set of interactive actions.  Buttons
 * send the associated command back to the AI via the store’s
 * analyzeAndExecute function.
 */
import React from 'react';
import { DesignCardData } from '../appStore';
import { useAppStore } from '../appStore';

interface DesignCardProps {
  card: DesignCardData;
}

const DesignCard: React.FC<DesignCardProps> = ({ card }) => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  return (
    <div className="w-full bg-white border border-gray-200 rounded-lg shadow p-4 space-y-3">
      {card.imageUrl && (
        <img
          src={card.imageUrl}
          alt={card.title}
          className="w-full h-32 object-cover rounded-md border"
        />
      )}
      <div>
        <h3 className="text-base font-semibold text-gray-900">{card.title}</h3>
        {card.description && (
          <p className="mt-1 text-sm text-gray-600 whitespace-pre-wrap">
            {card.description}
          </p>
        )}
      </div>
      {card.specs && card.specs.length > 0 && (
        <table className="w-full text-sm border-collapse">
          <tbody>
            {card.specs.map((spec) => (
              <tr key={spec.label} className="border-t border-gray-200">
                <td className="py-1 pr-4 font-medium text-gray-700 whitespace-nowrap">
                  {spec.label}
                </td>
                <td className="py-1 text-gray-900">{spec.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {card.actions && card.actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {card.actions.map((action) => (
            <button
              key={action.label}
              onClick={() => analyzeAndExecute(action.command)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium px-3 py-1 rounded-md transition-colors"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default DesignCard;

