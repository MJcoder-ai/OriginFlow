import { useState } from 'react';

const ChatInputArea = () => {
  const [input, setInput] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  return (
    <div
      className="grid-in-chat-input p-3 bg-white border-t border-white"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <textarea
        value={input}
        onChange={handleInputChange}
        placeholder="Type a message..."
        className="w-full h-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        rows={2}
      />
    </div>
  );
};

export default ChatInputArea;
