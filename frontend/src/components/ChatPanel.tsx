/**
 * File: frontend/src/components/ChatPanel.tsx
 * Panel containing the chat history and the main chat input component.
 */
import React, { useEffect, useRef } from 'react';
import { useAppStore } from '../appStore';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';
import { Loader } from 'lucide-react';

/** Wrapper panel that orchestrates the chat experience. */
const ChatPanel: React.FC = () => {
  const { messages, isAiProcessing } = useAppStore((state) => ({
    messages: state.messages,
    isAiProcessing: state.isAiProcessing,
  }));
  const chatHistoryRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom on new messages
  useEffect(() => {
    const chatHistory = chatHistoryRef.current;
    if (chatHistory) {
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }
  }, [messages, isAiProcessing]);

  return (
    <div className="flex flex-col h-full bg-white p-4">
      <div ref={chatHistoryRef} className="flex-grow overflow-y-auto mb-4 space-y-4 pr-2">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {isAiProcessing && (
          <div className="flex items-center justify-start space-x-3 p-2">
            <Loader className="animate-spin text-blue-600" size={18} />
            <span className="text-sm text-gray-500">AI is thinking...</span>
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
