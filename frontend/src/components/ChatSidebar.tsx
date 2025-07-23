import React from 'react';
import clsx from 'clsx';
import ChatPanel from './ChatPanel';
import PropertiesPanel from './PropertiesPanel';
import { useAppStore } from '../appStore';

/**
 * Sidebar containing the chat history and optional properties panel.
 */
interface ChatSidebarProps {
  /** Additional class names for positioning within a layout. */
  className?: string;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ className }) => {
  const selectedComponentId = useAppStore((s) => s.selectedComponentId);
  return (
    <aside className={clsx('w-[350px] flex flex-col h-full border-l bg-white', className)}>
      {selectedComponentId && (
        <div className="max-h-[250px] overflow-y-auto border-b p-4" role="dialog">
          <PropertiesPanel />
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50" aria-label="Chat history">
        <ChatPanel />
      </div>
    </aside>
  );
};

export default ChatSidebar;
