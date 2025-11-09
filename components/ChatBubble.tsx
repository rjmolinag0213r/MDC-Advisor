
import React from 'react';
import { Message } from '../types';

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  const bubbleClasses = isUser
    ? 'bg-blue-500 text-white self-end rounded-t-2xl rounded-bl-2xl'
    : 'bg-gray-200 text-gray-800 self-start rounded-t-2xl rounded-br-2xl';

  return (
    <div className={`max-w-[75%] lg:max-w-[65%] px-4 py-3 ${bubbleClasses} shadow-sm animate-fade-in-up`}>
      <p className="whitespace-pre-wrap">{message.text}</p>
    </div>
  );
};
