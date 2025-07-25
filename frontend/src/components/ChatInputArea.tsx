import { useAppStore } from '../appStore';

const ChatInputArea = () => {
  const input = useAppStore((s) => s.chatDraft);
  const setInput = useAppStore((s) => s.setChatDraft);
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const clearChatDraft = useAppStore((s) => s.clearChatDraft);

  return (
    <div
      className="grid-in-chat-input p-3 bg-white border-t border-white"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (input.trim()) {
              analyzeAndExecute(input);
              clearChatDraft();
            }
          }
        }}
        placeholder="Type a message..."
        className="w-full h-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        rows={2}
      />
    </div>
  );
};

export default ChatInputArea;
