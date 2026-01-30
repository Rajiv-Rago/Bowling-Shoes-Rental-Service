from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A tool call made by the assistant."""
    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result from a tool execution."""
    tool_call_id: str
    content: Any


class ChatMessage(BaseModel):
    """A single message in the conversation."""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Full conversation history."""
    messages: List[ChatMessage] = Field(default_factory=list)
    session_id: str


# WebSocket message types
class WSMessageType(str, Enum):
    # Client -> Server
    MESSAGE = "message"

    # Server -> Client
    STREAM_START = "stream_start"
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_RESULT = "tool_call_result"
    STREAM_END = "stream_end"
    ERROR = "error"


class WSClientMessage(BaseModel):
    """Message from client to server."""
    type: Literal["message"] = "message"
    content: str


class WSStreamStart(BaseModel):
    """Indicates stream is starting."""
    type: Literal["stream_start"] = "stream_start"


class WSTextDelta(BaseModel):
    """A chunk of streamed text."""
    type: Literal["text_delta"] = "text_delta"
    content: str


class WSToolCallStart(BaseModel):
    """Indicates a tool is being called."""
    type: Literal["tool_call_start"] = "tool_call_start"
    tool_call_id: str
    tool: str
    args: Dict[str, Any]


class WSToolCallResult(BaseModel):
    """Result from a tool call."""
    type: Literal["tool_call_result"] = "tool_call_result"
    tool_call_id: str
    tool: str
    result: Any
    success: bool = True


class WSStreamEnd(BaseModel):
    """Indicates stream has ended."""
    type: Literal["stream_end"] = "stream_end"


class WSError(BaseModel):
    """Error message."""
    type: Literal["error"] = "error"
    message: str
    code: Optional[str] = None


WSServerMessage = Union[
    WSStreamStart,
    WSTextDelta,
    WSToolCallStart,
    WSToolCallResult,
    WSStreamEnd,
    WSError
]
