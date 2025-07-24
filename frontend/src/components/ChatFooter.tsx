import { ArrowUp, Mic } from 'lucide-react';
import { useAppStore } from '../appStore';
import { FileUploadButton } from './FileUploadButton';

const ChatFooter = () => {
  const { analyzeAndExecute, setVoiceMode, chatDraft, clearChatDraft } = useAppStore();

  const handleSend = () => {
    const text = chatDraft.trim();
    if (text) {
      analyzeAndExecute(text);
      clearChatDraft();
    }
  };

  return (
    <div
      className="grid-in-chat-footer p-2 bg-white border-t border-white flex items-center gap-2"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <FileUploadButton />
      <button
        onClick={() => setVoiceMode('listening')}
        className="p-2 rounded-md hover:bg-gray-100"
        aria-label="Start voice input"
      >
        <Mic size={18} className="text-gray-600" />
      </button>
      <button
        onClick={handleSend}
        disabled={!chatDraft.trim()}
        className="ml-auto p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white flex items-center gap-2 text-sm px-4"
      >
        Send
        <ArrowUp size={16} />
      </button>
    </div>
  );
};

export default ChatFooter;
