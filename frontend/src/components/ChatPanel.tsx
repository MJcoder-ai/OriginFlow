/**
 * File: frontend/src/components/ChatPanel.tsx
 * A panel for interacting with an AI assistant, showing messages and an input box.
 */
import React from 'react';

/** Single chat message bubble. */
const ChatMessage: React.FC<{ author: string; children: React.ReactNode }> = ({ author, children }) => (
  <div>
    <span className="font-bold text-xs text-gray-600">{author}:</span>
    <div className="text-sm p-2 bg-gray-100 rounded-md mt-1">
      {children}
    </div>
  </div>
);

/** Panel containing chat history and message input. */
const ChatPanel: React.FC = () => {
  return (
    <div className="flex-grow flex flex-col p-2 overflow-hidden">
      {/* Chat History */}
      <div className="flex-grow space-y-4 overflow-y-auto p-2">
        <ChatMessage author="User">Hello, can you show the latest wireframe?</ChatMessage>
        <ChatMessage author="AI">Sure, here it is with chat functionality integrated.</ChatMessage>
      </div>
      {/* Chat Input */}
      <div className="mt-2">
        <input
          type="text"
          placeholder="Type a message..."
          className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
      </div>
    </div>
  );
};

export default ChatPanel;
