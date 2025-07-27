import { useAppStore } from '../appStore';
import { Mic, Send, Bot } from 'lucide-react';
import { FileUploadButton } from './FileUploadButton';
import React from 'react';

const ChatInputArea = () => {
  const input = useAppStore((s) => s.chatDraft);
  const setInput = useAppStore((s) => s.setChatDraft);
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const clearChatDraft = useAppStore((s) => s.clearChatDraft);
  const voiceMode = useAppStore((s) => s.voiceMode);
  const startListening = useAppStore((s) => s.startListening);
  const stopListening = useAppStore((s) => s.stopListening);
  const voiceTranscript = useAppStore((s) => s.voiceTranscript);
  const isAiProcessing = useAppStore((s) => s.isAiProcessing);

  const isListening = voiceMode === 'listening';
  const isSpeaking = voiceMode === 'speaking';

  return (
    <div
      className="grid-in-chat-input p-3 bg-white border-t border-white"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <div className="relative">
      <textarea
        value={isListening ? voiceTranscript : input}
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
        placeholder={isListening ? 'Listening...' : isSpeaking ? 'Echo is speaking...' : 'Ask Echo to do something...'}
        className="w-full h-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none pr-20"
        rows={2}
        readOnly={isListening || isSpeaking}
        />
        <div className="absolute right-2 bottom-2 flex gap-2">
          {/* File upload button (paperclip) */}
          <FileUploadButton />
          <button
            onClick={() => {
              if (isListening) {
                stopListening();
              } else {
              startListening();
            }
          }}
          className={`p-2 rounded-md ${isListening ? 'bg-red-600 text-white' : 'bg-gray-100'}`}
          aria-label="Record voice command"
          disabled={isAiProcessing || isSpeaking}
        >
          {isSpeaking ? <Bot className="h-5 w-5 animate-pulse" /> : <Mic className="h-5 w-5" />}
        </button>
        <button
          onClick={() => {
            if (input.trim()) {
              analyzeAndExecute(input);
              clearChatDraft();
            }
          }}
          disabled={isAiProcessing || isListening || isSpeaking}
          className="p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white"
          aria-label="Send message"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
      </div>
    </div>
  );
};

export default ChatInputArea;
