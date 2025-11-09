
import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import { ChatBubble } from './ChatBubble';
import { HikingIcon } from './icons/HikingIcon';
import { SendIcon } from './icons/SendIcon';

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = () => {
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="flex-1 lg:flex-2 flex flex-col bg-white">
      <header className="bg-blue-600 text-white p-4 flex items-center justify-center shadow-md z-10">
        <HikingIcon />
        <h1 className="text-xl font-bold ml-3">MyMDC.NextStop Chat</h1>
      </header>

      <div ref={chatContainerRef} className="flex-grow p-6 overflow-y-auto bg-slate-100">
        <div className="flex flex-col space-y-4">
          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="self-start flex items-center space-x-2">
                <div className="bg-gray-200 text-gray-800 rounded-t-2xl rounded-br-2xl p-3 flex items-center">
                    <span className="animate-pulse h-2 w-2 bg-slate-400 rounded-full mr-1.5"></span>
                    <span className="animate-pulse h-2 w-2 bg-slate-400 rounded-full mr-1.5" style={{animationDelay: '0.2s'}}></span>
                    <span className="animate-pulse h-2 w-2 bg-slate-400 rounded-full" style={{animationDelay: '0.4s'}}></span>
                </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="flex items-center space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-grow border border-gray-300 rounded-full py-3 px-5 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-shadow"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className="bg-blue-600 text-white rounded-full w-12 h-12 flex items-center justify-center hover:bg-blue-700 transition-colors disabled:bg-slate-400 disabled:cursor-not-allowed transform hover:scale-105"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
};
