import { useState } from 'react';
import { ArrowUp, Mic, Paperclip } from 'lucide-react';

const ChatFooter = () => {
  const [input, setInput] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  return (
    <div className="grid-in-chat-footer p-3 bg-white border-t border-gray-200 flex flex-col gap-2">
      <textarea
        value={input}
        onChange={handleInputChange}
        placeholder="Type a message..."
        className="w-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        rows={2}
      />
      <div className="flex justify-between items-center">
        <div className="flex gap-1">
          <button className="p-2 rounded-md hover:bg-gray-100"><Paperclip size={18} className="text-gray-600" /></button>
          <button className="p-2 rounded-md hover:bg-gray-100"><Mic size={18} className="text-gray-600" /></button>
        </div>
        <button className="p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white flex items-center gap-2 text-sm px-4">
          Send
          <ArrowUp size={16} />
        </button>
      </div>
    </div>
  );
};

export default ChatFooter;
