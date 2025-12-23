from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import logging

# Setup logging
logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Client connected: %s", websocket.client)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("Client disconnected: %s", websocket.client)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        await self.send_message(message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


class WebSocketService:
    """Service for managing WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.manager = websocket_manager

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await self.manager.connect(websocket)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        self.manager.disconnect(websocket)

    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected clients"""
        await self.manager.broadcast(message)

    async def broadcast_disaster_article(self, article: dict):
        """Broadcast a new disaster article to all connected clients"""
        message = {
            "event": "new_disaster_article",
            "data": article
        }
        await self.manager.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.manager.active_connections)


async def handle_disaster_feed(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


async def broadcast_disaster_article(article: dict):
    message = json.dumps({
        "event": "new_disaster_article",
        "data": article
    })
    await websocket_manager.send_message(message)