import { useState, useRef, useEffect } from 'react';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

export function MessageInput({ onSend, disabled, isStreaming }: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled && !isStreaming) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={isStreaming ? 'Waiting for response...' : 'Type a message...'}
        disabled={disabled || isStreaming}
        rows={1}
      />
      <button type="submit" disabled={disabled || isStreaming || !input.trim()}>
        {isStreaming ? 'Sending...' : 'Send'}
      </button>
    </form>
  );
}
