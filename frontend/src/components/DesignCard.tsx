/**
 * File: frontend/src/components/DesignCard.tsx
 * Enhanced design card with confidence scores, feedback buttons, and alternatives.
 * Integrates with the learning agent to track user preferences and improve suggestions.
 */
import React, { useState } from 'react';
import { DesignCardData } from '../appStore';
import { useAppStore } from '../appStore';
import { API_BASE_URL } from '../config';
import { useAppStore } from '../appStore';
import { 
  ThumbsUp, 
  ThumbsDown, 
  ChevronDown, 
  ChevronUp, 
  AlertCircle,
  CheckCircle,
  Info,
  Shuffle
} from 'lucide-react';

interface DesignCardProps {
  card: DesignCardData;
}

const DesignCard: React.FC<DesignCardProps> = ({ card }) => {
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const sessionId = useAppStore((s) => s.sessionId);
  const lastPrompt = useAppStore((s) => s.lastPrompt);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [userFeedback, setUserFeedback] = useState<'accepted' | 'rejected' | null>(null);
  
  // Helper to get confidence color and icon
  const getConfidenceDisplay = (confidence?: number) => {
    if (confidence === undefined) return null;
    
    const percentage = Math.round(confidence * 100);
    let color = 'text-gray-500';
    let bgColor = 'bg-gray-100';
    let Icon = Info;
    
    if (confidence >= 0.8) {
      color = 'text-green-600';
      bgColor = 'bg-green-100';
      Icon = CheckCircle;
    } else if (confidence >= 0.6) {
      color = 'text-blue-600';
      bgColor = 'bg-blue-100';
      Icon = Info;
    } else {
      color = 'text-yellow-600';
      bgColor = 'bg-yellow-100';
      Icon = AlertCircle;
    }
    
    return { percentage, color, bgColor, Icon };
  };
  
  const confidenceDisplay = getConfidenceDisplay(card.confidence);
  
  // Handle feedback submission
  const handleFeedback = async (feedback: 'accepted' | 'rejected', reason?: string) => {
    setUserFeedback(feedback);
    
    // Send feedback to learning agent
    try {
      await fetch(`${API_BASE_URL}/ai/log-feedback-v2`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_prompt: lastPrompt || '',
          proposed_action: {
            action: 'design_card_feedback',
            card_title: card.title,
            agent: card.agent,
          },
          user_decision: feedback === 'accepted' ? 'approved' : 'rejected',
          component_type: undefined,
          design_context: undefined,
          session_history: undefined,
          confidence_shown: card.confidence ?? null,
          confirmed_by: 'human',
        }),
      });
    } catch (error) {
      console.error('Failed to send feedback:', error);
    }
  };
  
  // Get button variant styles
  const getButtonStyle = (variant: string = 'primary') => {
    switch (variant) {
      case 'primary':
        return 'bg-blue-600 hover:bg-blue-700 text-white';
      case 'secondary':
        return 'bg-gray-200 hover:bg-gray-300 text-gray-800';
      case 'danger':
        return 'bg-red-600 hover:bg-red-700 text-white';
      default:
        return 'bg-blue-600 hover:bg-blue-700 text-white';
    }
  };

  return (
    <div className="w-full bg-white border border-gray-200 rounded-lg shadow hover:shadow-md transition-shadow duration-200">
      {/* Header with confidence and agent info */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-base font-semibold text-gray-900">{card.title}</h3>
            {card.agent && (
              <p className="text-xs text-gray-500 mt-1">
                Suggested by {card.agent}
              </p>
            )}
          </div>
          
          {/* Confidence indicator */}
          {confidenceDisplay && (
            <div className={`flex items-center space-x-2 px-2 py-1 rounded-md ${confidenceDisplay.bgColor}`}>
              <confidenceDisplay.Icon className={`w-4 h-4 ${confidenceDisplay.color}`} />
              <span className={`text-sm font-medium ${confidenceDisplay.color}`}>
                {confidenceDisplay.percentage}%
              </span>
            </div>
          )}
        </div>
        
        {card.description && (
          <p className="mt-2 text-sm text-gray-600 whitespace-pre-wrap">
            {card.description}
          </p>
        )}
      </div>
      
      {/* Image */}
      {card.imageUrl && (
        <div className="px-4 pt-4">
          <img
            src={card.imageUrl}
            alt={card.title}
            className="w-full h-32 object-cover rounded-md border"
          />
        </div>
      )}
      
      {/* Specs table */}
      {card.specs && card.specs.length > 0 && (
        <div className="px-4 py-3">
          <table className="w-full text-sm border-collapse">
            <tbody>
              {card.specs.map((spec) => (
                <tr key={spec.label} className="border-t border-gray-200 first:border-t-0">
                  <td className="py-2 pr-4 font-medium text-gray-700 whitespace-nowrap">
                    {spec.label}
                  </td>
                  <td className="py-2 text-gray-900">{spec.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Actions and feedback */}
      <div className="p-4 space-y-3">
        {/* Primary actions */}
        {card.actions && card.actions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {card.actions.map((action) => (
              <button
                key={action.label}
                onClick={() => {
                  analyzeAndExecute(action.command);
                  if (action.label.toLowerCase().includes('accept')) {
                    handleFeedback('accepted');
                  }
                }}
                className={`text-sm font-medium px-4 py-2 rounded-md transition-colors ${
                  getButtonStyle(action.variant)
                }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
        
        {/* Feedback buttons */}
        {!userFeedback && card.cardId && (
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">Is this suggestion helpful?</span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleFeedback('accepted')}
                className="flex items-center space-x-1 px-2 py-1 text-sm text-green-600 hover:bg-green-50 rounded transition-colors"
              >
                <ThumbsUp className="w-4 h-4" />
                <span>Yes</span>
              </button>
              <button
                onClick={() => handleFeedback('rejected')}
                className="flex items-center space-x-1 px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <ThumbsDown className="w-4 h-4" />
                <span>No</span>
              </button>
            </div>
          </div>
        )}
        
        {/* User feedback confirmation */}
        {userFeedback && (
          <div className="flex items-center space-x-2 pt-2 border-t border-gray-100">
            {userFeedback === 'accepted' ? (
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Thank you for the feedback!</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-orange-600">
                <Info className="w-4 h-4" />
                <span className="text-sm">We'll improve our suggestions</span>
              </div>
            )}
          </div>
        )}
        
        {/* Alternatives section */}
        {card.alternatives && card.alternatives.length > 0 && (
          <div className="pt-2 border-t border-gray-100">
            <button
              onClick={() => setShowAlternatives(!showAlternatives)}
              className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              <Shuffle className="w-4 h-4" />
              <span>See {card.alternatives.length} alternative{card.alternatives.length !== 1 ? 's' : ''}</span>
              {showAlternatives ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            
            {showAlternatives && (
              <div className="mt-3 space-y-2">
                {card.alternatives.map((alt, index) => {
                  const altConfidence = getConfidenceDisplay(alt.confidence);
                  return (
                    <div
                      key={index}
                      className="p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => analyzeAndExecute(alt.command)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">{alt.title}</h4>
                          <p className="text-xs text-gray-600 mt-1">{alt.description}</p>
                        </div>
                        {altConfidence && (
                          <span className={`text-xs px-2 py-1 rounded ${altConfidence.bgColor} ${altConfidence.color}`}>
                            {altConfidence.percentage}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DesignCard;

