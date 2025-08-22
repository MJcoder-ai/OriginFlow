import { useAppStore } from '../appStore';
import { Mic, Send, Bot } from 'lucide-react';
import { FileUploadButton } from './FileUploadButton';
import QuickActionBar from './QuickActionBar';
import ModeSelector from './ModeSelector';
import React from 'react';
import { confirmClose } from '../services/attributesApi';

const ChatInputArea = () => {
  const input = useAppStore((s) => s.chatDraft);
  const setInput = useAppStore((s) => s.setChatDraft);
  const analyzeAndExecute = useAppStore((s) => s.analyzeAndExecute);
  const clearChatDraft = useAppStore((s) => s.clearChatDraft);
  const planTasks = useAppStore((s) => s.planTasks);
  const runNextPlanTask = useAppStore((s) => s.runNextPlanTask);
  const voiceMode = useAppStore((s) => s.voiceMode);
  const startListening = useAppStore((s) => s.startListening);
  const stopListening = useAppStore((s) => s.stopListening);
  const voiceTranscript = useAppStore((s) => s.voiceTranscript);
  const isAiProcessing = useAppStore((s) => s.isAiProcessing);
  const activeDatasheet = useAppStore((s) => s.activeDatasheet);
  const setActiveDatasheet = useAppStore((s) => s.setActiveDatasheet);
  const addStatusMessage = useAppStore((s) => s.addStatusMessage);
  const setDatasheetDirty = useAppStore((s) => s.setDatasheetDirty);
  const resetOdlSession = useAppStore((s) => s.resetOdlSession);

  const isListening = voiceMode === 'listening';
  const isSpeaking = voiceMode === 'speaking';

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed) {
      const pending = planTasks.find((t) => t.status === 'pending');
      if (pending) await runNextPlanTask();
      clearChatDraft();
      return;
    }
    const normalized = trimmed.toLowerCase();
    if (
      activeDatasheet &&
      (normalized === 'confirm and close' || normalized === 'confirm & close')
    ) {
      try {
        await confirmClose(activeDatasheet.id);
        setActiveDatasheet(null);
        // Reset dirty flag after confirmation
        setDatasheetDirty(false);
        addStatusMessage('Datasheet confirmed', 'success');
      } catch (err) {
        console.error('Confirm & Close failed', err);
        addStatusMessage('Failed to confirm datasheet', 'error');
      }
      clearChatDraft();
      return;
    }
    analyzeAndExecute(trimmed);
    clearChatDraft();
  };

  return (
    <div
      className="grid-in-chat-input p-3 bg-white border-t border-white"
      style={{ borderLeft: '1px solid #e5e7eb' }}
    >
      {/* Quick actions appear above the input */}
      <QuickActionBar />
      {/* Mode selector aligns to the right on its own row */}
      <div className="flex justify-between items-center mt-2 mb-2">
        <ModeSelector />
      </div>
      <div className="relative">
        <textarea
          value={isListening ? voiceTranscript : input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void handleSend();
            }
          }}
          placeholder={
            isListening
              ? 'Listening...'
              : isSpeaking
              ? 'Echo is speaking...'
              : 'Ask Echo to do something...'
          }
          className="w-full h-full p-2 border border-gray-300 rounded bg-white text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none pr-24"
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
            {isSpeaking ? (
              <Bot className="h-5 w-5 animate-pulse" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </button>
          <button
            onClick={() => void handleSend()}
            disabled={isAiProcessing || isListening || isSpeaking}
            className="p-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 text-white"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
          {import.meta.env.DEV && (
            <button
              onClick={() => void resetOdlSession()}
              className="p-2 bg-gray-100 rounded-md"
              title="Reset session"
            >
              Reset
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInputArea;

