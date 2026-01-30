import json
from typing import Any, AsyncIterator, Dict, List, Optional
import logging

from anthropic import AsyncAnthropic

from .base import (
    BaseLLMProvider,
    LLMResponse,
    StreamChunk,
    ChunkType,
    ToolCallInfo,
    Message
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Tools should already be in Anthropic format."""
        return tools

    def format_messages(self, messages: List[Message]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Format messages for Anthropic API.

        Returns:
            Tuple of (system_message, formatted_messages)
        """
        system_content = None
        formatted = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            elif msg.role == "user":
                formatted.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                content = []
                if msg.content:
                    content.append({
                        "type": "text",
                        "text": msg.content
                    })
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments
                        })
                formatted.append({
                    "role": "assistant",
                    "content": content if content else msg.content
                })
            elif msg.role == "tool":
                formatted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": json.dumps(msg.tool_result) if isinstance(msg.tool_result, (dict, list)) else str(msg.tool_result)
                    }]
                })

        return system_content, formatted

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        system_content, formatted_messages = self.format_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_content:
            kwargs["system"] = system_content

        if tools:
            kwargs["tools"] = self.format_tools(tools)

        response = await self.client.messages.create(**kwargs)

        # Parse response
        content = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCallInfo(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[StreamChunk]:
        system_content, formatted_messages = self.format_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_content:
            kwargs["system"] = system_content

        if tools:
            kwargs["tools"] = self.format_tools(tools)

        current_tool_call: Optional[ToolCallInfo] = None
        current_tool_json = ""

        async with self.client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, 'type'):
                        if event.content_block.type == "tool_use":
                            current_tool_call = ToolCallInfo(
                                id=event.content_block.id,
                                name=event.content_block.name,
                                arguments={}
                            )
                            current_tool_json = ""
                            yield StreamChunk(
                                type=ChunkType.TOOL_CALL_START,
                                tool_call=current_tool_call
                            )

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        yield StreamChunk(
                            type=ChunkType.TEXT,
                            content=event.delta.text
                        )
                    elif hasattr(event.delta, 'partial_json'):
                        current_tool_json += event.delta.partial_json
                        yield StreamChunk(
                            type=ChunkType.TOOL_CALL_DELTA,
                            content=event.delta.partial_json
                        )

                elif event.type == "content_block_stop":
                    if current_tool_call is not None:
                        try:
                            current_tool_call.arguments = json.loads(current_tool_json) if current_tool_json else {}
                        except json.JSONDecodeError:
                            current_tool_call.arguments = {}
                        current_tool_call.arguments_json = current_tool_json
                        yield StreamChunk(
                            type=ChunkType.TOOL_CALL_END,
                            tool_call=current_tool_call
                        )
                        current_tool_call = None
                        current_tool_json = ""

                elif event.type == "message_stop":
                    yield StreamChunk(type=ChunkType.DONE)
