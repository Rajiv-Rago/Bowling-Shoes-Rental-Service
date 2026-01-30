import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types/chat';
import { Message } from './Message';

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <div className="welcome-message">
          <h2>Welcome to the Bowling Shoes Rental Service!</h2>
          <p>I can help you with:</p>
          <ul>
            <li>Creating a new customer account</li>
            <li>Renting bowling shoes</li>
            <li>Checking your rental history</li>
            <li>Information about pricing and discounts</li>
          </ul>
          <p>How can I assist you today?</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list" ref={listRef}>
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
    </div>
  );
}
