from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class ChunkType(str, Enum):
    """Type of content in a stream chunk."""
    TEXT = "text"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_END = "tool_call_end"
    DONE = "done"
    ERROR = "error"


@dataclass
class ToolCallInfo:
    """Information about a tool call."""
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    arguments_json: str = ""  # Raw JSON string (for streaming)


@dataclass
class StreamChunk:
    """A chunk of streamed response."""
    type: ChunkType
    content: Optional[str] = None
    tool_call: Optional[ToolCallInfo] = None
    error: Optional[str] = None


@dataclass
class LLMResponse:
    """Complete response from an LLM."""
    content: Optional[str] = None
    tool_calls: List[ToolCallInfo] = field(default_factory=list)
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class Message:
    """A message in the conversation."""

    def __init__(
        self,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCallInfo]] = None,
        tool_call_id: Optional[str] = None,
        tool_result: Optional[Any] = None
    ):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id
        self.tool_result = tool_result

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: Optional[str] = None, tool_calls: Optional[List[ToolCallInfo]] = None) -> "Message":
        return cls(role="assistant", content=content, tool_calls=tool_calls)

    @classmethod
    def tool_result(cls, tool_call_id: str, result: Any) -> "Message":
        return cls(role="tool", tool_call_id=tool_call_id, tool_result=result)

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role="system", content=content)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers (Anthropic, OpenAI, Groq) must implement this interface.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model to use for this provider."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of this provider."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """Send a chat request and get a complete response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Complete LLM response
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[StreamChunk]:
        """Send a chat request and stream the response.

        Args:
            messages: List of conversation messages
            tools: Optional list of tool definitions
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Yields:
            Stream chunks as they arrive
        """
        pass

    @abstractmethod
    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for this specific provider.

        Args:
            tools: Tools in generic format

        Returns:
            Tools in provider-specific format
        """
        pass

    @abstractmethod
    def format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for this specific provider.

        Args:
            messages: Messages in generic format

        Returns:
            Messages in provider-specific format
        """
        pass
