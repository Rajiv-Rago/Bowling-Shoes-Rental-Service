"""Conversation context management for the agent."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from ..llm.base import Message, ToolCallInfo

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Manages conversation history and state for a session.

    Each WebSocket connection gets its own ConversationContext to track
    the conversation history and any session-specific state.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation."""
        self.messages.append(Message.system(content))

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.messages.append(Message.user(content))
        logger.debug(f"[{self.session_id}] User: {content[:100]}...")

    def add_assistant_message(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCallInfo]] = None
    ) -> None:
        """Add an assistant message to the conversation."""
        self.messages.append(Message.assistant(content=content, tool_calls=tool_calls))
        if content:
            logger.debug(f"[{self.session_id}] Assistant: {content[:100]}...")
        if tool_calls:
            logger.debug(f"[{self.session_id}] Tool calls: {[tc.name for tc in tool_calls]}")

    def add_tool_result(self, tool_call_id: str, result: Any) -> None:
        """Add a tool result to the conversation."""
        self.messages.append(Message.tool_result(tool_call_id, result))
        logger.debug(f"[{self.session_id}] Tool result for {tool_call_id}")

    def get_messages(self) -> List[Message]:
        """Get all messages in the conversation."""
        return self.messages.copy()

    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages)

    def clear(self) -> None:
        """Clear the conversation history (keeps system messages)."""
        system_messages = [m for m in self.messages if m.role == "system"]
        self.messages = system_messages

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the context to a dictionary."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ContextManager:
    """Manages multiple conversation contexts.

    Useful for tracking multiple concurrent WebSocket sessions.
    """

    def __init__(self):
        self._contexts: Dict[str, ConversationContext] = {}

    def create_context(self, session_id: Optional[str] = None) -> ConversationContext:
        """Create a new conversation context."""
        context = ConversationContext(
            session_id=session_id or str(uuid.uuid4())
        )
        self._contexts[context.session_id] = context
        logger.info(f"Created context: {context.session_id}")
        return context

    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get a context by session ID."""
        return self._contexts.get(session_id)

    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create a new one."""
        if session_id in self._contexts:
            return self._contexts[session_id]
        return self.create_context(session_id)

    def remove_context(self, session_id: str) -> None:
        """Remove a context."""
        if session_id in self._contexts:
            del self._contexts[session_id]
            logger.info(f"Removed context: {session_id}")

    def list_contexts(self) -> List[str]:
        """List all active session IDs."""
        return list(self._contexts.keys())

    def context_count(self) -> int:
        """Get the number of active contexts."""
        return len(self._contexts)


# Global context manager instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
