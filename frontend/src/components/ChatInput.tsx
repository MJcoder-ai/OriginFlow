import { useState } from 'react';
import { ArrowUp, Mic, Paperclip, Wand2, Repeat } from 'lucide-react';
import { useAppStore } from '../appStore';

export const ChatInput: React.FC = () => {
  const [input, setInput] = useState('');
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const isAiProcessing = useAppStore((s) => s.isAiProcessing);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSend = () => {
    if (input.trim()) {
      analyzeAndExecute(input);
      setInput('');
    }
  };

  return (
    <div className="grid-in-chatInput p-3 bg-white border-t border-white flex flex-col gap-2">
      <textarea
        value={input}
        onChange={handleInputChange}
        placeholder="Type a message..."
        className="w-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        rows={3}
        disabled={isAiProcessing}
      />
      <div className="flex justify-between items-center">
        <div className="flex gap-1">
          <button className="p-2 rounded-md hover:bg-gray-100"><Paperclip size={18} className="text-gray-600" /></button>
          <button className="p-2 rounded-md hover:bg-gray-100"><Mic size={18} className="text-gray-600" /></button>
          <button className="p-2 rounded-md hover:bg-gray-100"><Wand2 size={18} className="text-gray-600" /></button>
          <button className="p-2 rounded-md hover:bg-gray-100"><Repeat size={18} className="text-gray-600" /></button>
        </div>
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          className="p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white flex items-center gap-2 text-sm px-4"
        >
          Send
          <ArrowUp size={16} />
        </button>
      </div>
    </div>
  );
};
