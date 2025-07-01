# src/api/routes/chat.py

import json
import uuid
from typing import Dict, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from ...db.database import Database
from ...db.services.llm_service import LLMService, ConversationManager
from ..middleware.rate_limiter import get_rate_limit_stats, RateLimitConfig

router = APIRouter()

# Database dependency
async def get_db():
    async with Database.get_session() as session:
        yield session

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}")
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_message(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(json.dumps(message))

manager = ConnectionManager()

# Pydantic models for API
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: datetime
    sources: Optional[list] = None

class ConversationSummary(BaseModel):
    conversation_id: str
    last_message: str
    timestamp: datetime
    message_count: int


async def _get_redis_client():
    """Helper function to get Redis client with error handling."""
    import redis.asyncio as redis
    from ...config.vector_config import REDIS_URL
    
    redis_client = None
    try:
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()  # Test connection
        return redis_client
    except Exception as e:
        logger.warning(f"Redis connection failed for LLM service: {e}")
        return None


@router.websocket("/ws/chat/{connection_id}")
async def chat_websocket(
    websocket: WebSocket, 
    connection_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat with streaming responses.
    """
    await manager.connect(websocket, connection_id)
    
    try:
        # Initialize Redis client for LLM service
        redis_client = await _get_redis_client()
        
        # Initialize LLM service for this connection
        llm_service = LLMService(session, redis_client=redis_client)
        conversation_manager = ConversationManager(redis_client)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            conversation_id = message_data.get("conversation_id") or str(uuid.uuid4())
            
            if not user_message.strip():
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Empty message received",
                    "timestamp": datetime.now().isoformat()
                }))
                continue
            
            # Send acknowledgment
            await websocket.send_text(json.dumps({
                "type": "message_received",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Load conversation history
            history = await conversation_manager.load_conversation(conversation_id)
            if history:
                llm_service.memory.chat_memory.messages = history
            
            # Send typing indicator
            await websocket.send_text(json.dumps({
                "type": "typing",
                "timestamp": datetime.now().isoformat()
            }))
            
            try:
                # Process message with streaming
                full_response = ""
                async for chunk in llm_service.chat(
                    message=user_message,
                    conversation_id=conversation_id,
                    websocket=websocket
                ):
                    full_response += chunk
                
                # Save conversation
                await conversation_manager.save_conversation(
                    conversation_id, 
                    llm_service.memory.chat_memory.messages
                )
                
                # Send completion signal
                await websocket.send_text(json.dumps({
                    "type": "message_complete",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }))
                
            except Exception as e:
                logger.error(f"Error processing chat message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Error processing your message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"Client {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        manager.disconnect(connection_id)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_message: ChatMessage,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """
    REST endpoint for chat - non-streaming alternative to WebSocket.
    """
    try:
        conversation_id = chat_message.conversation_id or str(uuid.uuid4())
        
        # Initialize Redis client for LLM service
        redis_client = await _get_redis_client()
        
        # Initialize services
        llm_service = LLMService(session, redis_client=redis_client)
        conversation_manager = ConversationManager(redis_client)
        
        # Load conversation history
        history = await conversation_manager.load_conversation(conversation_id)
        if history:
            llm_service.memory.chat_memory.messages = history
        
        # Process message
        full_response = ""
        async for chunk in llm_service.chat(
            message=chat_message.message,
            conversation_id=conversation_id
        ):
            full_response += chunk
        
        # Save conversation in background
        background_tasks.add_task(
            conversation_manager.save_conversation,
            conversation_id,
            llm_service.memory.chat_memory.messages
        )
        
        return ChatResponse(
            response=full_response,
            conversation_id=conversation_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stream")
async def chat_stream(
    message: str,
    conversation_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """
    Streaming chat endpoint using Server-Sent Events.
    """
    conversation_id_final = conversation_id or str(uuid.uuid4())
    
    async def generate_response():
        try:
            # Initialize Redis client for LLM service
            redis_client = await _get_redis_client()
            
            # Initialize services
            llm_service = LLMService(session, redis_client=redis_client)
            conversation_manager = ConversationManager(redis_client)
            
            # Load conversation history
            history = await conversation_manager.load_conversation(conversation_id_final)
            if history:
                llm_service.memory.chat_memory.messages = history
            
            # Send initial metadata
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id_final})}\n\n"
            
            # Stream response chunks
            async for chunk in llm_service.chat(
                message=message,
                conversation_id=conversation_id_final
            ):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Save conversation
            await conversation_manager.save_conversation(
                conversation_id_final,
                llm_service.memory.chat_memory.messages
            )
            
            # Send completion
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Get conversation history.
    """
    try:
        redis_client = await _get_redis_client()
        conversation_manager = ConversationManager(redis_client)
        messages = await conversation_manager.load_conversation(conversation_id)
        
        # Format messages for response
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "type": "human" if msg.__class__.__name__ == "HumanMessage" else "ai",
                "content": msg.content,
                "timestamp": datetime.now().isoformat()  # This would be stored in real implementation
            })
        
        return {
            "conversation_id": conversation_id,
            "messages": formatted_messages,
            "message_count": len(formatted_messages)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Delete conversation history.
    """
    try:
        redis_client = await _get_redis_client()
        conversation_manager = ConversationManager(redis_client)
        # In a real implementation, you'd delete from Redis/database
        # For now, we'll just clear the memory
        
        return {
            "message": f"Conversation {conversation_id} deleted successfully",
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
async def list_conversations(
    user_id: Optional[str] = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_db)
):
    """
    List recent conversations for a user.
    """
    try:
        # In a real implementation, you'd query from database
        # This is a placeholder that would need proper implementation
        
        return {
            "conversations": [],
            "total": 0,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/feedback")
async def chat_feedback(
    conversation_id: str,
    message_id: str,
    feedback: str,  # "thumbs_up", "thumbs_down", etc.
    comment: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for chat responses.
    """
    try:
        # Store feedback in database for improving the system
        # This would be implemented based on your feedback schema
        
        logger.info(f"Feedback received for conversation {conversation_id}: {feedback}")
        
        return {
            "message": "Feedback submitted successfully",
            "conversation_id": conversation_id,
            "feedback": feedback
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_chat_statistics():
    """Get rate limiting and cache statistics for chat endpoints."""
    try:
        # Get rate limiting stats
        rate_stats = await get_rate_limit_stats()
        
        # Get LLM cache stats if available
        llm_stats = {}
        try:
            # Create temporary LLM service to get cache stats
            async with Database.get_session() as session:
                redis_client = await _get_redis_client()
                llm_service = LLMService(session, redis_client=redis_client)
                llm_stats = llm_service.get_cache_statistics()
        except Exception as e:
            logger.warning(f"Could not get LLM cache stats: {e}")
            llm_stats = {"error": "Cache statistics unavailable"}
        
        return {
            "rate_limiting": rate_stats,
            "llm_cache": llm_stats,
            "rate_limit_config": {
                "tiers": RateLimitConfig.RATE_LIMITS,
                "window_duration_hours": RateLimitConfig.WINDOW_DURATION // 3600,
                "default_tier": RateLimitConfig.DEFAULT_TIER
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/rate-limit/classify")
async def classify_query_for_caching(query: str):
    """Test endpoint to see how a query would be classified for caching purposes."""
    try:
        async with Database.get_session() as session:
            redis_client = await _get_redis_client()
            llm_service = LLMService(session, redis_client=redis_client)
            classification = llm_service.classify_query(query)
            return classification
    except Exception as e:
        logger.error(f"Failed to classify query: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify query") 