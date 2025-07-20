/**
 * File: frontend/src/components/ChatInput.tsx
 * Dedicated input component for the chat panel with voice mode support.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../appStore';
import { Wand2, Mic } from 'lucide-react';
import { FileUploadButton } from './FileUploadButton';
import clsx from 'clsx';

/** Input box for sending chat messages and toggling voice mode. */
export const ChatInput: React.FC = () => {
  const { isAiProcessing, analyzeAndExecute } = useAppStore((state) => ({
    isAiProcessing: state.isAiProcessing,
    analyzeAndExecute: state.analyzeAndExecute,
  }));

  const [message, setMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

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
        setMessage((prev) => prev + finalTranscript);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, []);

  const handleSendMessage = async () => {
    if (message.trim() === '' || isAiProcessing) return;
    const commandToSend = message;
    setMessage('');
    await analyzeAndExecute(commandToSend);
  };

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
    }
    setIsListening(!isListening);
  };

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
          placeholder="Type a message or click the mic to dictate..."
          className="w-full h-10 px-3 pr-20 text-sm bg-gray-100 border border-transparent rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          disabled={isAiProcessing}
        />
        <div className="absolute top-0 right-0 flex items-center h-full mr-3">
          <button
            onClick={toggleListen}
            className={clsx('p-2 text-gray-500 hover:text-blue-600', isListening && 'text-red-500')}
            disabled={!recognitionRef.current}
          >
            <Mic size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};
