import React from 'react';
import clsx from 'clsx';
import ChatPanel from './ChatPanel';
import { ChatInput } from './ChatInput';

/**
 * Sidebar containing the chat history and input box.
 */
interface ChatSidebarProps {
  /** Additional class names for positioning within a layout. */
  className?: string;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ className }) => (
  <div className={clsx('w-[350px] h-full flex flex-col border-l bg-white', className)}>
    <div className="flex-1 overflow-y-auto">
      <ChatPanel />
    </div>
    <div className="border-t">
      <ChatInput />
    </div>
  </div>
);

export default ChatSidebar;
