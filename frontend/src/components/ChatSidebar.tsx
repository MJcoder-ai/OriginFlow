import React from 'react';
import ChatPanel from './ChatPanel';

/** Simple wrapper for the chat history panel. */
const ChatSidebar: React.FC = () => {
  return (
    <aside className="w-[350px] flex flex-col h-full border-l bg-white [grid-area:chat]">
      <ChatPanel />
    </aside>
  );
};

export default ChatSidebar;
