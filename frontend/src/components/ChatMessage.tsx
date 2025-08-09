/**
 * File: frontend/src/components/ChatMessage.tsx
 * Renders a single chat message with left/right justification.
 */
import React from 'react';
import clsx from 'clsx';
import { Message } from '../appStore';
import DesignCard from './DesignCard';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  // Render rich card messages when provided.  Cards are rendered
  // independently of author alignment since they occupy the full width of
  // the chat column.
  if (message.card) {
    return (
      <div className="w-full flex justify-start my-2">
        <DesignCard card={message.card} />
      </div>
    );
  }

  // Status messages (e.g. system notices) are rendered in the centre with
  // neutral styling to differentiate them from the conversation.
  if (message.type === 'status') {
    return (
      <div className="w-full flex justify-center my-2">
        <div className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-md text-xs font-medium">
          {message.text}
        </div>
      </div>
    );
  }

  const isUser = message.author === 'User';
  return (
    <div className={clsx('w-full flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[80%] rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap break-words',
          {
            'bg-blue-600 text-white': isUser,
            'bg-gray-200 text-gray-800': !isUser,
          }
        )}
      >
        {message.text}
      </div>
    </div>
  );
};
