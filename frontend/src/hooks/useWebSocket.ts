import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  WSServerMessage,
  WSClientMessage,
  ChatMessage,
  ConnectionStatus,
  ToolCall,
} from '../types/chat';

interface UseWebSocketOptions {
  sessionId: string;
  onMessage?: (message: WSServerMessage) => void;
}

export function useWebSocket({ sessionId, onMessage }: UseWebSocketOptions) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const currentMessageRef = useRef<ChatMessage | null>(null);
  const pendingToolCallsRef = useRef<Map<string, ToolCall>>(new Map());
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/chat/ws/${sessionId}`);

    ws.onopen = () => {
      setStatus('connected');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onclose = () => {
      setStatus('disconnected');
      wsRef.current = null;

      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = () => {
      setStatus('error');
    };

    ws.onmessage = (event) => {
      try {
        const data: WSServerMessage = JSON.parse(event.data);
        handleServerMessage(data);
        onMessage?.(data);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    wsRef.current = ws;
  }, [sessionId, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('disconnected');
  }, []);

  const handleServerMessage = useCallback((msg: WSServerMessage) => {
    switch (msg.type) {
      case 'stream_start':
        setIsStreaming(true);
        currentMessageRef.current = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: '',
          toolCalls: [],
          timestamp: new Date(),
          isStreaming: true,
        };
        pendingToolCallsRef.current.clear();
        setMessages((prev) => [...prev, currentMessageRef.current!]);
        break;

      case 'text_delta':
        if (currentMessageRef.current) {
          currentMessageRef.current.content += msg.content;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentMessageRef.current!.id
                ? { ...currentMessageRef.current! }
                : m
            )
          );
        }
        break;

      case 'tool_call_start':
        if (currentMessageRef.current) {
          const toolCall: ToolCall = {
            id: msg.tool_call_id,
            name: msg.tool,
            args: msg.args,
          };
          pendingToolCallsRef.current.set(msg.tool_call_id, toolCall);
          currentMessageRef.current.toolCalls = [
            ...(currentMessageRef.current.toolCalls || []),
            toolCall,
          ];
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentMessageRef.current!.id
                ? { ...currentMessageRef.current! }
                : m
            )
          );
        }
        break;

      case 'tool_call_result':
        if (currentMessageRef.current) {
          const existingCall = pendingToolCallsRef.current.get(msg.tool_call_id);
          if (existingCall) {
            existingCall.result = msg.result;
            existingCall.success = msg.success;
          }
          currentMessageRef.current.toolCalls = currentMessageRef.current.toolCalls?.map(
            (tc) =>
              tc.id === msg.tool_call_id
                ? { ...tc, result: msg.result, success: msg.success }
                : tc
          );
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentMessageRef.current!.id
                ? { ...currentMessageRef.current! }
                : m
            )
          );
        }
        break;

      case 'stream_end':
        setIsStreaming(false);
        if (currentMessageRef.current) {
          currentMessageRef.current.isStreaming = false;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentMessageRef.current!.id
                ? { ...currentMessageRef.current!, isStreaming: false }
                : m
            )
          );
        }
        currentMessageRef.current = null;
        break;

      case 'error':
        setIsStreaming(false);
        if (currentMessageRef.current) {
          currentMessageRef.current.content += `\n\nError: ${msg.message}`;
          currentMessageRef.current.isStreaming = false;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === currentMessageRef.current!.id
                ? { ...currentMessageRef.current! }
                : m
            )
          );
        }
        currentMessageRef.current = null;
        break;
    }
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    // Add user message to UI
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to server
    const wsMessage: WSClientMessage = {
      type: 'message',
      content,
    };
    wsRef.current.send(JSON.stringify(wsMessage));
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    status,
    messages,
    isStreaming,
    sendMessage,
    clearMessages,
    connect,
    disconnect,
  };
}
