import { ArrowUp, Mic, Paperclip } from 'lucide-react';

const ChatFooter = () => {
  return (
    <div
      className="grid-in-chat-footer p-3 bg-white border-t border-white flex items-center justify-between"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <div className="flex gap-1">
        <button className="p-2 rounded-md hover:bg-gray-100">
          <Paperclip size={18} className="text-gray-600" />
        </button>
        <button className="p-2 rounded-md hover:bg-gray-100">
          <Mic size={18} className="text-gray-600" />
        </button>
      </div>
      <button className="p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white flex items-center gap-2 text-sm px-4">
        Send
        <ArrowUp size={16} />
      </button>
    </div>
  );
};

export default ChatFooter;
