/**
 * File: frontend/src/components/ChatMessage.tsx
 * Renders a single chat message with left/right justification.
 */
import React from 'react';
import clsx from 'clsx';
import { Message } from '../appStore';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.author === 'User';

  return (
    <div className={clsx('w-full flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx('max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap', {
          'bg-blue-600 text-white': isUser,
          'bg-gray-200 text-gray-800': !isUser,
        })}
      >
        {message.text}
      </div>
    </div>
  );
};
