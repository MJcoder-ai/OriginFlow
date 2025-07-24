import React from 'react';
import ChatPanel from './ChatPanel';

/** Simple wrapper for the chat history panel. */
const ChatSidebar: React.FC = () => {
  return (
    // The chat sidebar width is dictated by the grid column definition (350px).
    // Remove the hard-coded width here so it naturally fills its grid cell.
    <aside className="flex flex-col h-full border-l bg-white [grid-area:chat]">
      <ChatPanel />
    </aside>
  );
};

export default ChatSidebar;
