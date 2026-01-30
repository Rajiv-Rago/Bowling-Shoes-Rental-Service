"""Agent engine for orchestrating LLM and tools."""

from typing import Any, AsyncIterator, Callable, Dict, List, Optional
import logging
import json

from .context import ConversationContext
from .prompts import SYSTEM_PROMPT
from ..llm.base import BaseLLMProvider, ChunkType, StreamChunk, ToolCallInfo, Message
from ..llm.factory import get_provider
from ..tools.base import ToolContext
from ..tools.registry import ToolRegistry, get_registry
from ..schemas.tools import ToolCallRequest

logger = logging.getLogger(__name__)


class AgentEngine:
    """Orchestrates the conversation between user, LLM, and tools.

    The engine implements the agent loop:
    1. User sends message
    2. LLM processes and optionally calls tools
    3. Tools execute and return results
    4. LLM continues until it produces a final response
    5. Response is streamed back to user
    """

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        registry: Optional[ToolRegistry] = None,
        system_prompt: str = SYSTEM_PROMPT,
        max_iterations: int = 10
    ):
        self.provider = provider or get_provider()
        self.registry = registry or get_registry()
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    async def process_message(
        self,
        user_message: str,
        context: ConversationContext,
        on_chunk: Optional[Callable[[StreamChunk], None]] = None
    ) -> str:
        """Process a user message and return the final response.

        This is a non-streaming version that collects all chunks.

        Args:
            user_message: The user's message
            context: Conversation context
            on_chunk: Optional callback for each chunk

        Returns:
            The complete assistant response
        """
        full_response = ""

        async for chunk in self.process_message_stream(user_message, context):
            if on_chunk:
                on_chunk(chunk)

            if chunk.type == ChunkType.TEXT:
                full_response += chunk.content or ""

        return full_response

    async def process_message_stream(
        self,
        user_message: str,
        context: ConversationContext
    ) -> AsyncIterator[StreamChunk]:
        """Process a user message and stream the response.

        Implements the full agent loop with tool execution.

        Args:
            user_message: The user's message
            context: Conversation context

        Yields:
            Stream chunks (text, tool calls, tool results, etc.)
        """
        # Ensure system prompt is in context
        if not any(m.role == "system" for m in context.messages):
            context.add_system_message(self.system_prompt)

        # Add user message
        context.add_user_message(user_message)

        # Get tool definitions
        tools = self.registry.get_definitions_anthropic()

        # Agent loop
        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1

            # Stream LLM response
            collected_text = ""
            collected_tool_calls: List[ToolCallInfo] = []

            try:
                async for chunk in self.provider.chat_stream(
                    messages=context.get_messages(),
                    tools=tools,
                    temperature=0.7,
                    max_tokens=4096
                ):
                    # Forward text chunks
                    if chunk.type == ChunkType.TEXT:
                        collected_text += chunk.content or ""
                        yield chunk

                    # Forward tool call events
                    elif chunk.type == ChunkType.TOOL_CALL_START:
                        yield chunk

                    elif chunk.type == ChunkType.TOOL_CALL_DELTA:
                        yield chunk

                    elif chunk.type == ChunkType.TOOL_CALL_END:
                        if chunk.tool_call:
                            collected_tool_calls.append(chunk.tool_call)
                        yield chunk

                    elif chunk.type == ChunkType.ERROR:
                        yield chunk
                        return

            except Exception as e:
                logger.exception("Error in LLM stream")
                yield StreamChunk(type=ChunkType.ERROR, error=str(e))
                return

            # Add assistant message to context
            context.add_assistant_message(
                content=collected_text if collected_text else None,
                tool_calls=collected_tool_calls if collected_tool_calls else None
            )

            # If no tool calls, we're done
            if not collected_tool_calls:
                yield StreamChunk(type=ChunkType.DONE)
                return

            # Execute tool calls
            tool_context = ToolContext(session_id=context.session_id)

            for tool_call in collected_tool_calls:
                logger.info(f"Executing tool: {tool_call.name}")

                request = ToolCallRequest(
                    tool_name=tool_call.name,
                    tool_call_id=tool_call.id,
                    arguments=tool_call.arguments
                )

                result = await self.registry.execute(request, tool_context)

                # Add to context
                context.add_tool_result(tool_call.id, result.result if result.success else {"error": result.error})

                # Yield result event
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=""  # Placeholder - actual result is in the tool result message
                )

            # Continue loop to let LLM process tool results

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        yield StreamChunk(type=ChunkType.DONE)


# Global engine instance
_engine: Optional[AgentEngine] = None


def get_engine() -> AgentEngine:
    """Get the global agent engine."""
    global _engine
    if _engine is None:
        _engine = AgentEngine()
    return _engine


def reset_engine() -> None:
    """Reset the global engine (useful for testing)."""
    global _engine
    _engine = None
