import React, { useRef } from 'react';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Mic, Send, Bot, Paperclip } from 'lucide-react';
import { useAppStore } from '../appStore';

const ChatInputArea = () => {
  const input = useAppStore((s) => s.chatDraft);
  const setInput = useAppStore((s) => s.setChatDraft);
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const clearChatDraft = useAppStore((s) => s.clearChatDraft);
  const voiceMode = useAppStore((s) => s.voiceMode);
  const startListening = useAppStore((s) => s.startListening);
  const stopListening = useAppStore((s) => s.stopListening);
  const toggleFileStagingArea = useAppStore((s) => s.toggleFileStagingArea);
  const addStagedFiles = useAppStore((s) => s.addStagedFiles);
  const voiceTranscript = useAppStore((s) => s.voiceTranscript);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (input.trim()) {
      analyzeAndExecute(input);
      clearChatDraft();
    }
  };

  const handleMicClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleAttachClick = (e: React.MouseEvent) => {
    e.preventDefault();
    fileInputRef.current?.click();
    toggleFileStagingArea();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addStagedFiles(Array.from(e.target.files));
    }
  };

  const isListening = voiceMode === 'listening';
  const isSpeaking = voiceMode === 'speaking';

  return (
    <div
      className="grid-in-chat-input p-3 bg-white border-t border-white"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      <div className="relative">
      <Textarea
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
        className="w-full h-full resize-none pr-20"
        rows={2}
        readOnly={isListening || isSpeaking}
      />
        <div className="absolute right-2 bottom-2 flex gap-2">
          <Button
            onClick={handleAttachClick}
            size="icon"
            variant="ghost"
            disabled={isListening || isSpeaking}
            aria-label="Attach file"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Button
            onClick={handleMicClick}
            size="icon"
            variant={isListening ? 'destructive' : 'ghost'}
            disabled={isSpeaking}
            aria-label="Record voice command"
          >
            {isSpeaking ? <Bot className="h-5 w-5 animate-pulse" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Button
            onClick={handleSend}
            disabled={isListening || isSpeaking}
            size="icon"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            multiple
          />
        </div>
      </div>
    </div>
  );
};

export default ChatInputArea;
