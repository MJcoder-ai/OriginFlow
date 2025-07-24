import React from 'react';

/** Simple wrapper for the chat history panel. */
const ChatSidebar: React.FC = () => {
  return (
    <aside className="grid-in-chat flex flex-col h-full border-l border-gray-200 bg-white">
      {/* This component acts as a wrapper for the chat area, but the actual content (Panel and Input) is placed directly by the Layout grid. */}
    </aside>
  );
};

export default ChatSidebar;
