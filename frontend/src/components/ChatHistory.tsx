import { useAppStore } from '../appStore';
import ChatMessage from './ChatMessage';

const ChatHistory = () => {
  const messages = useAppStore((state) => state.messages);

  return (
    <div className="grid-in-chat-history flex flex-col h-full bg-white overflow-y-auto min-h-0 border-l border-gray-200">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, index) => (
          <ChatMessage key={index} message={m} />
        ))}
      </div>
    </div>
  );
};

export default ChatHistory;
