import { useAppStore } from '../appStore';
import { ChatMessage } from './ChatMessage';
import { Loader2 } from 'lucide-react';
import PlanTimeline from './PlanTimeline';

const ChatHistory = () => {
  const messages = useAppStore((state) => state.messages);
  const isProcessing = useAppStore((s) => s.isAiProcessing);

  return (
    <div
      className="grid-in-chat-history flex flex-col h-full bg-white overflow-y-auto min-h-0"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      {/* Timeline of planned tasks */}
      <PlanTimeline />
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, index) => (
          <ChatMessage key={index} message={m} />
        ))}
        {isProcessing && (
          <div
            className="w-full flex justify-start mt-2"
            aria-live="polite"
            aria-label="AI processing indicator"
          >
            <div className="flex items-center space-x-2 bg-gray-200 text-gray-800 px-4 py-2 rounded-2xl text-sm">
              <Loader2 className="animate-spin h-4 w-4" />
              <span>Echo is thinking…</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatHistory;
