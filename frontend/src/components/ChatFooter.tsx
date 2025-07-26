import React from 'react';
import { useAppStore } from '../appStore';

const ChatFooter: React.FC = () => {
  const {
    voiceOutputEnabled,
    toggleVoiceOutput,
    isContinuousConversation,
    toggleContinuousConversation,
  } = useAppStore();

  return (
    <div className="p-4 border-t border-gray-200">
      <div className="flex justify-between items-center gap-4">
        <div className="flex items-center space-x-2">
          <input
            id="voice-output"
            type="checkbox"
            className="form-checkbox"
            checked={voiceOutputEnabled}
            onChange={toggleVoiceOutput}
          />
          <label htmlFor="voice-output" className="text-sm font-medium">
            Voice Output
          </label>
        </div>
        <div className="flex items-center space-x-2">
          <input
            id="continuous-conversation"
            type="checkbox"
            className="form-checkbox"
            checked={isContinuousConversation}
            onChange={toggleContinuousConversation}
          />
          <label htmlFor="continuous-conversation" className="text-sm font-medium">
            Continuous Conversation
          </label>
        </div>
      </div>
      <p className="mt-4 text-xs text-gray-500">
        OriginFlow is a prototype. Responses may be inaccurate.
      </p>
    </div>
  );
};

export default ChatFooter;
