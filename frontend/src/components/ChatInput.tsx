/**
 * File: frontend/src/components/ChatInput.tsx
 * Dedicated input component for the chat panel with voice mode support.
 */
import React, { useState } from 'react';
import { useAppStore } from '../appStore';
import { Wand2, Mic, Waves } from 'lucide-react';
import { FileUploadButton } from './FileUploadButton';

/** Input box for sending chat messages and toggling voice mode. */
export const ChatInput: React.FC = () => {
  const { chatMode, setChatMode, isAiProcessing, analyzeAndExecute } = useAppStore(
    (state) => ({
      chatMode: state.chatMode,
      setChatMode: state.setChatMode,
      isAiProcessing: state.isAiProcessing,
      analyzeAndExecute: state.analyzeAndExecute,
    }),
  );

  const [message, setMessage] = useState('');

  const handleSendMessage = async () => {
    if (message.trim() === '' || isAiProcessing) return;
    const commandToSend = message;
    setMessage('');
    await analyzeAndExecute(commandToSend);
  };

  // Hide voice/dictation icons when user is typing
  const showVoiceIcons = message.length === 0;

  return (
    <div className="relative flex items-center w-full">
      <FileUploadButton />
      <button className="p-2 mr-2 text-gray-500 hover:text-blue-600 transition-colors">
        <Wand2 size={20} />
      </button>

      <div className="relative w-full">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type a message..."
          className="w-full h-10 px-3 pr-20 text-sm bg-gray-100 border border-transparent rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          disabled={isAiProcessing}
        />
        {showVoiceIcons && (
          <div className="absolute top-0 right-0 flex items-center h-full mr-3">
            <button className="p-2 text-gray-500 hover:text-blue-600"><Mic size={20} /></button>
            <button className="p-2 text-gray-500 hover:text-blue-600"><Waves size={20} /></button>
          </div>
        )}
      </div>
    </div>
  );
};
