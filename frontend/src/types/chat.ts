// WebSocket message types

export type WSMessageType =
  | 'message'
  | 'stream_start'
  | 'text_delta'
  | 'tool_call_start'
  | 'tool_call_result'
  | 'stream_end'
  | 'error';

// Client -> Server
export interface WSClientMessage {
  type: 'message';
  content: string;
}

// Server -> Client
export interface WSStreamStart {
  type: 'stream_start';
}

export interface WSTextDelta {
  type: 'text_delta';
  content: string;
}

export interface WSToolCallStart {
  type: 'tool_call_start';
  tool_call_id: string;
  tool: string;
  args: Record<string, unknown>;
}

export interface WSToolCallResult {
  type: 'tool_call_result';
  tool_call_id: string;
  tool: string;
  result: unknown;
  success: boolean;
}

export interface WSStreamEnd {
  type: 'stream_end';
}

export interface WSError {
  type: 'error';
  message: string;
  code?: string;
}

export type WSServerMessage =
  | WSStreamStart
  | WSTextDelta
  | WSToolCallStart
  | WSToolCallResult
  | WSStreamEnd
  | WSError;

// UI types
export type MessageRole = 'user' | 'assistant' | 'tool';

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: unknown;
  success?: boolean;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  toolCalls?: ToolCall[];
  timestamp: Date;
  isStreaming?: boolean;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
