import { useMemo } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import type { ConnectionStatus } from '../types/chat';

function StatusIndicator({ status }: { status: ConnectionStatus }) {
  const statusText = {
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
    error: 'Connection Error',
  };

  return (
    <div className={`status-indicator ${status}`}>
      <span className="status-dot" />
      <span className="status-text">{statusText[status]}</span>
    </div>
  );
}

export function Chat() {
  const sessionId = useMemo(() => {
    // Use stored session ID or create new one
    let id = localStorage.getItem('chatSessionId');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('chatSessionId', id);
    }
    return id;
  }, []);

  const {
    status,
    messages,
    isStreaming,
    sendMessage,
    clearMessages,
  } = useWebSocket({ sessionId });

  const handleNewChat = () => {
    // Generate new session ID
    const newId = crypto.randomUUID();
    localStorage.setItem('chatSessionId', newId);
    // Reload to start fresh
    window.location.reload();
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Bowling Shoes Rental</h1>
        <div className="header-actions">
          <StatusIndicator status={status} />
          <button
            className="clear-button"
            onClick={clearMessages}
            title="Clear messages"
          >
            Clear
          </button>
          <button
            className="new-chat-button"
            onClick={handleNewChat}
            title="Start new chat"
          >
            New Chat
          </button>
        </div>
      </header>

      <MessageList messages={messages} />

      <MessageInput
        onSend={sendMessage}
        disabled={status !== 'connected'}
        isStreaming={isStreaming}
      />
    </div>
  );
}
