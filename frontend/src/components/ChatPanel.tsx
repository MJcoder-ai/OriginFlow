/**
 * File: frontend/src/components/ChatPanel.tsx
 * Panel containing the chat history and the main chat input component.
 */
import React, { useEffect, useRef } from 'react';
import { useAppStore } from '../appStore';
import { Loader } from 'lucide-react';

/** Wrapper panel that orchestrates the chat experience. */
const ChatPanel: React.FC = () => {
  const { messages, isAiProcessing } = useAppStore((state) => ({
    messages: state.messages,
    isAiProcessing: state.isAiProcessing,
  }));
  const endRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const isAtBottom =
      containerRef.current &&
      containerRef.current.scrollHeight - containerRef.current.scrollTop <=
        containerRef.current.clientHeight + 50;

    if (isAtBottom) scrollToBottom();
  }, [messages]);

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-2">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`p-2 rounded text-sm max-w-[80%] ${msg.author === 'User' ? 'ml-auto bg-blue-100 text-blue-900' : 'mr-auto bg-gray-100 text-gray-800'}`}
        >
          {msg.text}
        </div>
      ))}
      {isAiProcessing && (
        <div className="flex items-center justify-start space-x-3 p-2">
          <Loader className="animate-spin text-blue-600" size={18} />
          <span className="text-sm text-gray-500">AI is thinking...</span>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
};

export default ChatPanel;
