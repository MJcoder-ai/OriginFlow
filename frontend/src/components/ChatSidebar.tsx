import React from 'react';
import clsx from 'clsx';
import ChatPanel from './ChatPanel';
import { ChatInput } from './ChatInput';
import PropertiesPanel from './PropertiesPanel';
import { useAppStore } from '../appStore';

/**
 * Sidebar containing the chat history and input box.
 */
interface ChatSidebarProps {
  /** Additional class names for positioning within a layout. */
  className?: string;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ className }) => {
  const selectedComponentId = useAppStore((s) => s.selectedComponentId);
  return (
    <aside className={clsx('w-[350px] h-full flex flex-col border-l bg-white', className)}>
      {selectedComponentId && <PropertiesPanel />}
      <div className="flex-1 overflow-y-auto px-4 py-2">
        <ChatPanel />
      </div>
      <div className="border-t px-4 py-2">
        <ChatInput />
      </div>
    </aside>
  );
};

export default ChatSidebar;
