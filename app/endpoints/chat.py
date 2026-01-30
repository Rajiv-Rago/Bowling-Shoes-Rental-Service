"""WebSocket chat endpoint for the bowling shoe rental agent."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..agent.engine import get_engine
from ..agent.context import get_context_manager, ConversationContext
from ..llm.base import ChunkType
from ..schemas.chat import (
    WSClientMessage,
    WSStreamStart,
    WSTextDelta,
    WSToolCallStart,
    WSToolCallResult,
    WSStreamEnd,
    WSError
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str) -> None:
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_json(self, session_id: str, data: dict) -> None:
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for chat interactions.

    Messages from client:
        {"type": "message", "content": "user message here"}

    Messages to client:
        {"type": "stream_start"}
        {"type": "text_delta", "content": "chunk of text"}
        {"type": "tool_call_start", "tool_call_id": "...", "tool": "...", "args": {...}}
        {"type": "tool_call_result", "tool_call_id": "...", "tool": "...", "result": {...}}
        {"type": "stream_end"}
        {"type": "error", "message": "error description"}
    """
    await manager.connect(websocket, session_id)

    # Get or create conversation context
    context_manager = get_context_manager()
    context = context_manager.get_or_create_context(session_id)

    # Get agent engine
    engine = get_engine()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            try:
                client_msg = WSClientMessage(**data)
            except Exception as e:
                await websocket.send_json(
                    WSError(message=f"Invalid message format: {e}").model_dump()
                )
                continue

            # Start streaming
            await websocket.send_json(WSStreamStart().model_dump())

            # Track tool calls for proper result delivery
            pending_tool_calls = {}

            try:
                async for chunk in engine.process_message_stream(
                    client_msg.content,
                    context
                ):
                    if chunk.type == ChunkType.TEXT and chunk.content:
                        await websocket.send_json(
                            WSTextDelta(content=chunk.content).model_dump()
                        )

                    elif chunk.type == ChunkType.TOOL_CALL_START and chunk.tool_call:
                        pending_tool_calls[chunk.tool_call.id] = chunk.tool_call.name
                        await websocket.send_json(
                            WSToolCallStart(
                                tool_call_id=chunk.tool_call.id,
                                tool=chunk.tool_call.name,
                                args=chunk.tool_call.arguments
                            ).model_dump()
                        )

                    elif chunk.type == ChunkType.TOOL_CALL_END and chunk.tool_call:
                        # Send complete tool call info
                        await websocket.send_json(
                            WSToolCallStart(
                                tool_call_id=chunk.tool_call.id,
                                tool=chunk.tool_call.name,
                                args=chunk.tool_call.arguments
                            ).model_dump()
                        )

                        # The actual result will come from context after execution
                        # For now, we'll send the result after the agent loop processes it
                        # Get the last tool result from context
                        for msg in reversed(context.messages):
                            if msg.role == "tool" and msg.tool_call_id == chunk.tool_call.id:
                                await websocket.send_json(
                                    WSToolCallResult(
                                        tool_call_id=chunk.tool_call.id,
                                        tool=chunk.tool_call.name,
                                        result=msg.tool_result,
                                        success=not isinstance(msg.tool_result, dict) or "error" not in msg.tool_result
                                    ).model_dump()
                                )
                                break

                    elif chunk.type == ChunkType.DONE:
                        await websocket.send_json(WSStreamEnd().model_dump())

                    elif chunk.type == ChunkType.ERROR:
                        await websocket.send_json(
                            WSError(message=chunk.error or "Unknown error").model_dump()
                        )

            except Exception as e:
                logger.exception("Error processing message")
                await websocket.send_json(
                    WSError(message=str(e)).model_dump()
                )
                await websocket.send_json(WSStreamEnd().model_dump())

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        context_manager.remove_context(session_id)


@router.get("/sessions")
async def list_sessions():
    """List active chat sessions."""
    context_manager = get_context_manager()
    return {
        "sessions": context_manager.list_contexts(),
        "count": context_manager.context_count()
    }


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session's history."""
    context_manager = get_context_manager()
    context = context_manager.get_context(session_id)
    if context:
        context.clear()
        return {"message": f"Session {session_id} cleared"}
    return {"message": f"Session {session_id} not found"}
