/**
 * File: frontend/src/components/ChatPanel.tsx
 * A panel for interacting with an AI assistant with local state management.
 */
import React, { useState, KeyboardEvent } from 'react';
import clsx from 'clsx';

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
  // Local state for managing messages and the current input value
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, author: 'AI', text: "Hello! How can I help you with your design?" },
  ]);
  const [inputValue, setInputValue] = useState('');

  const handleSendMessage = () => {
    if (inputValue.trim() === '') return;

    // Add the user's message
    const userMessage: Message = {
      id: Date.now(),
      author: 'User',
      text: inputValue,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue(''); // Clear the input

    // Simulate an AI response after a short delay
    setTimeout(() => {
      const aiResponse: Message = {
        id: Date.now() + 1,
        author: 'AI',
        text: "That's an interesting idea. Let me look into the specifications for that component.",
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="flex-grow flex flex-col p-2 overflow-hidden">
      {/* Chat History */}
      <div className="flex-grow space-y-3 overflow-y-auto p-2 flex flex-col">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
      </div>
      {/* Chat Input */}
      <div className="mt-2">
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
