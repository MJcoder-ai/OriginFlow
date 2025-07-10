/**
 * File: frontend/src/components/ChatInput.tsx
 * Dedicated input component for the chat panel with voice mode support.
 */
import React, { useState } from 'react';
import { useAppStore } from '../appStore';
import { Paperclip, Wand2, Mic, Waves, SendHorizonal, Square } from 'lucide-react';

/** Input box for sending chat messages and toggling voice mode. */
export const ChatInput: React.FC = () => {
  const { chatMode, setChatMode, isAiProcessing } = useAppStore();
  const [message, setMessage] = useState('');

  const handleSendMessage = () => {
    if (message.trim() === '') return;
    console.log('Sending message:', message);
    setMessage('');
  };

  const isVoiceMode = chatMode === 'voice';
  const placeholderText = isVoiceMode ? 'Listening...' : 'Type a message, or use a tool...';
  const containerClasses = `
    flex items-center p-2 bg-gray-50 rounded-full
    border border-gray-200 transition-all duration-300
    focus-within:ring-2 focus-within:ring-blue-500
    ${isVoiceMode ? 'ring-2 ring-blue-500 shadow-lg' : ''}
  `;

  return (
    <div className={containerClasses}>
      <button className="p-2 text-gray-500 hover:text-blue-600 transition-colors">
        <Paperclip size={20} />
      </button>
      <button className="p-2 text-gray-500 hover:text-blue-600 transition-colors">
        <Wand2 size={20} />
      </button>

      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
        placeholder={placeholderText}
        className="flex-grow bg-transparent focus:outline-none mx-2 text-gray-800"
        disabled={isVoiceMode}
      />

      <button className="p-2 text-gray-500 hover:text-blue-600 transition-colors">
        <Mic size={20} />
      </button>
      <button
        onClick={() => setChatMode(isVoiceMode ? 'default' : 'voice')}
        className={`p-2 transition-colors ${isVoiceMode ? 'text-blue-600' : 'text-gray-500 hover:text-blue-600'}`}
      >
        <Waves size={20} />
      </button>

      {isVoiceMode ? (
        <button
          onClick={() => setChatMode('default')}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-all ml-2"
        >
          <Square size={20} />
        </button>
      ) : (
        <button
          onClick={handleSendMessage}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-all ml-2 disabled:bg-gray-400"
          disabled={!message.trim() || isAiProcessing}
        >
          <SendHorizonal size={20} />
        </button>
      )}
    </div>
  );
};
