import type { ChatMessage } from '../types/chat';
import { ToolCallDisplay } from './ToolCallDisplay';

interface MessageProps {
  message: ChatMessage;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`message ${message.role}`}>
      <div className="message-header">
        <span className="message-role">
          {isUser ? 'You' : 'Assistant'}
        </span>
        <span className="message-time">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>

      <div className="message-content">
        {message.content || (message.isStreaming && !message.content && '...')}
        {message.isStreaming && <span className="cursor">|</span>}
      </div>

      {isAssistant && message.toolCalls && message.toolCalls.length > 0 && (
        <div className="tool-calls">
          {message.toolCalls.map((toolCall) => (
            <ToolCallDisplay key={toolCall.id} toolCall={toolCall} />
          ))}
        </div>
      )}
    </div>
  );
}
