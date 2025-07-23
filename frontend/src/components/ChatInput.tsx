/**
 * File: frontend/src/components/ChatInput.tsx
 * Dedicated input component for the chat panel with voice mode support.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../appStore';
import { Wand2, Mic, Repeat } from 'lucide-react';
import { FileUploadButton } from './FileUploadButton';
import clsx from 'clsx';

/** Input box for sending chat messages and toggling voice mode. */
export const ChatInput: React.FC = () => {
  const { isAiProcessing, analyzeAndExecute } = useAppStore((state) => ({
    isAiProcessing: state.isAiProcessing,
    analyzeAndExecute: state.analyzeAndExecute,
  }));
  const { voiceMode, setVoiceMode, isContinuousConversation, toggleContinuousConversation } =
    useAppStore();

  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const speechTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-resize the textarea based on its scroll height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  // When voice mode switches to processing, submit the current message
  useEffect(() => {
    if (voiceMode === 'processing' && message.trim() !== '') {
      analyzeAndExecute(message);
      setMessage('');
    }
  }, [voiceMode, message, analyzeAndExecute]);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech Recognition not supported in this browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        if (finalTranscript.toLowerCase().includes('stop listening')) {
          setVoiceMode('idle');
          if (isContinuousConversation) {
            toggleContinuousConversation();
          }
          setMessage('');
          return;
        }
        setMessage((prev) => prev + finalTranscript);
      }
    };

    recognition.onend = () => {
      if (speechTimeoutRef.current) {
        clearTimeout(speechTimeoutRef.current);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, [setVoiceMode, isContinuousConversation, toggleContinuousConversation]);

  // Timer logic for detecting pause in speech input
  useEffect(() => {
    if (voiceMode === 'listening' && message.trim() !== '') {
      if (speechTimeoutRef.current) {
        clearTimeout(speechTimeoutRef.current);
      }
      speechTimeoutRef.current = setTimeout(() => {
        setVoiceMode('processing');
      }, 2000);
    }
  }, [message, voiceMode, setVoiceMode]);

  // Control the recognition engine based on voiceMode
  useEffect(() => {
    if (voiceMode === 'listening') {
      recognitionRef.current?.start();
    } else {
      recognitionRef.current?.stop();
    }
  }, [voiceMode]);

  const toggleListen = () => {
    setVoiceMode(voiceMode === 'listening' ? 'idle' : 'listening');
  };

  const handleTextSubmit = () => {
    if (message.trim() !== '') {
      analyzeAndExecute(message);
      setMessage('');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleTextSubmit();
  };



  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 px-4 py-2">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleTextSubmit();
            }
          }}
          aria-label="Compose message"
          placeholder="Type a message or click the mic to dictate..."
          className="w-full resize-none overflow-hidden min-h-[32px] max-h-[120px] py-2 px-3 pr-20 text-sm bg-gray-100 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isAiProcessing}
          rows={1}
        />
        <div className="absolute top-0 right-0 flex items-center h-full mr-3 gap-1">
          <FileUploadButton />
          <button className="p-2 text-gray-500 hover:text-blue-600 transition-colors" type="button">
            <Wand2 size={20} />
          </button>
          <button
            onClick={toggleContinuousConversation}
            type="button"
            className={clsx('p-2 text-gray-500 hover:text-blue-600', isContinuousConversation && 'text-blue-500')}
          >
            <Repeat size={16} />
          </button>
          <button
            onClick={toggleListen}
            type="button"
            className={clsx('p-2 text-gray-500 hover:text-blue-600', voiceMode === 'listening' && 'text-red-500')}
            disabled={!recognitionRef.current}
          >
            <Mic size={20} />
          </button>
        </div>
      </div>
      <div className="flex justify-end">
        <button type="submit" className="btn-primary">
          Send
        </button>
      </div>
    </form>
  );
};

