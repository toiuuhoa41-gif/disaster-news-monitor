"""
WebSocket Disaster Feed with Redis Pub/Sub for Scalability
Supports multiple workers/instances
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Set, Optional
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections with Redis pub/sub support.
    Enables horizontal scaling across multiple workers.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.redis_connected: bool = False
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")
        
        # Send welcome message
        await self._send_to_socket(websocket, {
            "event": "connected",
            "data": {
                "message": "Connected to Disaster Monitor realtime feed",
                "timestamp": datetime.utcnow().isoformat(),
                "total_connections": len(self.active_connections)
            }
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def _send_to_socket(self, websocket: WebSocket, data: dict):
        """Send data to a specific WebSocket"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast message with topic filtering (future enhancement)"""
        message["topic"] = topic
        await self.broadcast(message)
    
    async def start_heartbeat(self, interval: int = 30):
        """Start heartbeat to keep connections alive"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(interval))
    
    async def _heartbeat_loop(self, interval: int):
        """Send periodic heartbeats"""
        while True:
            try:
                await asyncio.sleep(interval)
                await self.broadcast({
                    "event": "heartbeat",
                    "data": {"timestamp": datetime.utcnow().isoformat()}
                })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def setup_redis_subscriber(self):
        """Setup Redis pub/sub subscription for scaling"""
        try:
            from mongodb.api.services.redis_service import (
                RedisService, 
                CHANNEL_NEW_ARTICLE, 
                CHANNEL_ALERT,
                CHANNEL_STATS_UPDATE
            )
            
            await RedisService.connect()
            
            # Subscribe to channels
            await RedisService.subscribe(CHANNEL_NEW_ARTICLE, self._on_redis_message)
            await RedisService.subscribe(CHANNEL_ALERT, self._on_redis_message)
            await RedisService.subscribe(CHANNEL_STATS_UPDATE, self._on_redis_message)
            
            self.redis_connected = True
            logger.info("📡 WebSocket connected to Redis pub/sub")
            
        except Exception as e:
            logger.warning(f"Redis pub/sub not available: {e}. Using local broadcast only.")
            self.redis_connected = False
    
    async def _on_redis_message(self, message: dict):
        """Handle messages from Redis pub/sub"""
        await self.broadcast(message)
    
    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/disasters")
async def disaster_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time disaster updates.
    
    Events:
    - connected: Initial connection acknowledgment
    - heartbeat: Keep-alive ping
    - new_disaster_article: New article detected
    - disaster_alert: High severity alert
    - stats_update: Statistics update
    """
    await manager.connect(websocket)
    
    try:
        # Start heartbeat if not running
        await manager.start_heartbeat()
        
        while True:
            try:
                # Wait for client messages (pings, subscriptions, etc.)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60  # Client should ping within this time
                )
                
                # Handle client messages
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "event": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })
                elif data.get("type") == "subscribe":
                    # Future: topic-based subscriptions
                    topics = data.get("topics", [])
                    await websocket.send_json({
                        "event": "subscribed",
                        "data": {"topics": topics}
                    })
                    
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_json({
                        "event": "ping",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })
                except:
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status"""
    return {
        "active_connections": manager.connection_count,
        "redis_connected": manager.redis_connected,
        "timestamp": datetime.utcnow().isoformat()
    }


# ========================================
# Broadcasting Functions
# ========================================

async def broadcast_disaster_article(article: dict):
    """
    Broadcast a new disaster article to all connected clients.
    Uses Redis if available for multi-worker support.
    """
    message = {
        "event": "new_disaster_article",
        "data": article,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if manager.redis_connected:
        from mongodb.api.services.redis_service import publish_new_article
        await publish_new_article(article)
    else:
        await manager.broadcast(message)


async def broadcast_alert(alert: dict):
    """Broadcast disaster alert"""
    message = {
        "event": "disaster_alert",
        "data": alert,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if manager.redis_connected:
        from mongodb.api.services.redis_service import publish_alert
        await publish_alert(alert)
    else:
        await manager.broadcast(message)


async def broadcast_stats(stats: dict):
    """Broadcast statistics update"""
    message = {
        "event": "stats_update",
        "data": stats,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if manager.redis_connected:
        from mongodb.api.services.redis_service import publish_stats_update
        await publish_stats_update(stats)
    else:
        await manager.broadcast(message)


# Legacy function for backward compatibility
async def on_new_disaster_article(article: dict):
    """Trigger broadcasting when a new article is crawled"""
    await broadcast_disaster_article(article)