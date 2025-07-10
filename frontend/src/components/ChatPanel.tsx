/**
 * File: frontend/src/components/ChatPanel.tsx
 * A panel for interacting with an AI assistant with local state management.
 */
import React, { useState, KeyboardEvent } from 'react';
import clsx from 'clsx';
import { api } from '../services/api';
import { useAppStore } from '../appStore';
import { AiAction } from '../types/ai';

// Define the shape of a single chat message
interface Message {
  id: number;
  author: 'User' | 'AI';
  text: string;
}

// Sub-component for rendering a single message
const ChatMessage: React.FC<{ message: Message }> = ({ message }) => (
  <div
    className={clsx('max-w-[80%] rounded-lg px-3 py-2 text-sm', {
      'bg-blue-500 text-white self-end': message.author === 'User',
      'bg-gray-200 text-gray-800 self-start': message.author === 'AI',
    })}
  >
    {message.text}
  </div>
);

const ChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const { executeAiActions } = useAppStore();

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const command = inputValue.trim();

    // 1️⃣ add user bubble
    const userMsg: Message = {
      id: Date.now(),
      author: 'User',
      text: command,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');

    try {
      if (/analyse|analyze|validate|organize/i.test(command)) {
        const snapshot = {
          components: useAppStore.getState().canvasComponents,
          links: useAppStore.getState().links,
        };
        const acts = await api.analyzeDesign(snapshot, command);
        await executeAiActions(acts);
        return;
      }

      // 2️⃣ ask the backend
      const actions: AiAction[] = await api.sendCommandToAI(command);

      // 3️⃣ show "thinking…" bubble
      const aiMsg: Message = {
        id: Date.now() + 1,
        author: 'AI',
        text: 'Executing changes…',
      };
      setMessages((prev) => [...prev, aiMsg]);

      // 4️⃣ apply to canvas & state
      await executeAiActions(actions);

      // 5️⃣ replace provisional message with success summary
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsg.id ? { ...m, text: `Added ${actions.length} item(s) ✅` } : m,
        ),
      );
    } catch (err) {
      console.error(err);
      const errorMsg: Message = {
        id: Date.now() + 2,
        author: 'AI',
        text: 'Sorry, something went wrong 🤖',
      };
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    // Fill the parent container to keep the overall panel height fixed
    <div className="w-full h-full flex flex-col p-2">
      {/* Chat History: grows and becomes scrollable when content overflows */}
      <div className="flex-grow space-y-3 overflow-y-auto p-2">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>

      {/* Chat Input pinned to the bottom */}
      <div className="mt-2 flex-shrink-0">
        <input
          type="text"
          placeholder="Type a message..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
      </div>
    </div>
  );
};

export default ChatPanel;
