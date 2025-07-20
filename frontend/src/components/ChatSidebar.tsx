import React from 'react';
import ChatPanel from './ChatPanel';
import { ChatInput } from './ChatInput';

/**
 * Sidebar containing the chat history and input box.
 */
const ChatSidebar: React.FC = () => (
  <div className="w-[350px] h-full flex flex-col border-l bg-white shadow-inner">
    <div className="flex-grow overflow-y-auto">
      <ChatPanel />
    </div>
    <div className="border-t p-2">
      <ChatInput />
    </div>
  </div>
);

export default ChatSidebar;
