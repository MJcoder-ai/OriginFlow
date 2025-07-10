/**
 * File: frontend/src/components/ChatPanel.tsx
 * Simple panel wrapping chat history and input box.
 */
import React from 'react';
import { useAppStore } from '../appStore';
import { ChatInput } from './ChatInput';
import { Loader } from 'lucide-react';

/** Wrapper panel containing history and input. */
const ChatPanel: React.FC = () => {
  const { isAiProcessing } = useAppStore();

  return (
    <div className="flex flex-col h-full bg-white p-4">
      <div className="flex-grow overflow-y-auto mb-4">
        <p className="text-sm text-gray-500">Your chat history goes here...</p>
        {isAiProcessing && (
          <div className="flex items-center justify-start space-x-2 p-2">
            <Loader className="animate-spin text-blue-600" size={20} />
            <span className="text-sm text-gray-600">AI is thinking...</span>
          </div>
        )}
      </div>
      <div className="mt-auto">
        <ChatInput />
      </div>
    </div>
  );
};

export default ChatPanel;
