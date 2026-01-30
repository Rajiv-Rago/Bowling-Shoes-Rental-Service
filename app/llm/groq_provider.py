import json
from typing import Any, AsyncIterator, Dict, List, Optional
import logging

from groq import AsyncGroq

from .base import (
    BaseLLMProvider,
    LLMResponse,
    StreamChunk,
    ChunkType,
    ToolCallInfo,
    Message
)

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq provider implementation (OpenAI-compatible)."""

    @property
    def default_model(self) -> str:
        return "llama-3.1-70b-versatile"

    @property
    def provider_name(self) -> str:
        return "groq"

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = AsyncGroq(api_key=api_key)

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert to OpenAI function calling format (Groq uses same format)."""
        formatted = []
        for tool in tools:
            if "type" in tool and tool["type"] == "function":
                formatted.append(tool)
            else:
                formatted.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("input_schema", {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    }
                })
        return formatted

    def format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Format messages for Groq API (OpenAI-compatible)."""
        formatted = []

        for msg in messages:
            if msg.role == "system":
                formatted.append({
                    "role": "system",
                    "content": msg.content
                })
            elif msg.role == "user":
                formatted.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                message = {"role": "assistant"}
                if msg.content:
                    message["content"] = msg.content
                if msg.tool_calls:
                    message["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments)
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                formatted.append(message)
            elif msg.role == "tool":
                formatted.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": json.dumps(msg.tool_result) if isinstance(msg.tool_result, (dict, list)) else str(msg.tool_result)
                })

        return formatted

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> LLMResponse:
        formatted_messages = self.format_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if tools:
            kwargs["tools"] = self.format_tools(tools)

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        content = choice.message.content
        tool_calls = []

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCallInfo(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments) if tc.function.arguments else {}
                ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            } if response.usage else None
        )

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> AsyncIterator[StreamChunk]:
        formatted_messages = self.format_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        if tools:
            kwargs["tools"] = self.format_tools(tools)

        tool_calls_in_progress: Dict[int, ToolCallInfo] = {}
        tool_call_args: Dict[int, str] = {}

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=delta.content
                )

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index

                    if tc.id:
                        tool_calls_in_progress[idx] = ToolCallInfo(
                            id=tc.id,
                            name=tc.function.name if tc.function else "",
                            arguments={}
                        )
                        tool_call_args[idx] = ""
                        yield StreamChunk(
                            type=ChunkType.TOOL_CALL_START,
                            tool_call=tool_calls_in_progress[idx]
                        )

                    if tc.function and tc.function.arguments:
                        tool_call_args[idx] = tool_call_args.get(idx, "") + tc.function.arguments
                        yield StreamChunk(
                            type=ChunkType.TOOL_CALL_DELTA,
                            content=tc.function.arguments
                        )

            if chunk.choices[0].finish_reason:
                for idx, tc in tool_calls_in_progress.items():
                    try:
                        tc.arguments = json.loads(tool_call_args.get(idx, "{}"))
                    except json.JSONDecodeError:
                        tc.arguments = {}
                    tc.arguments_json = tool_call_args.get(idx, "")
                    yield StreamChunk(
                        type=ChunkType.TOOL_CALL_END,
                        tool_call=tc
                    )

                yield StreamChunk(type=ChunkType.DONE)
