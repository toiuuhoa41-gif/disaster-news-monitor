"""
Realtime Router - WebSocket endpoints cho disaster feed realtime

Endpoints:
- GET /realtime/ - Test page cho WebSocket
- WS /realtime/ws/disasters - WebSocket feed thiên tai
- GET /realtime/status - Trạng thái kết nối
- GET /realtime/recent - Bài báo thiên tai gần đây
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

from mongodb.api.services.websocket_service import WebSocketService, websocket_manager
from mongodb.api.config.database import Database

router = APIRouter()

# WebSocket service uses global manager, so single instance is fine
websocket_service = WebSocketService()


@router.get("/", response_class=HTMLResponse)
async def get_realtime_page():
    """Test page cho WebSocket connection"""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Disaster Monitor - Realtime Feed</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: #1a1a2e; color: #fff; }
                h1 { color: #e94560; }
                .status { padding: 10px; border-radius: 5px; margin-bottom: 20px; }
                .connected { background: #2ecc71; }
                .disconnected { background: #e74c3c; }
                #messages { list-style: none; padding: 0; }
                #messages li { 
                    background: #16213e; 
                    margin: 10px 0; 
                    padding: 15px; 
                    border-radius: 5px;
                    border-left: 4px solid #e94560;
                }
                .severity-high { border-left-color: #e74c3c; }
                .severity-medium { border-left-color: #f39c12; }
                .severity-low { border-left-color: #3498db; }
                .meta { font-size: 12px; color: #888; margin-top: 5px; }
            </style>
        </head>
        <body>
            <h1>🌊 Disaster Monitor - Realtime Feed</h1>
            <div id="status" class="status disconnected">Connecting...</div>
            <h2>Recent Disasters</h2>
            <ul id="messages"></ul>
            
            <script>
                const statusEl = document.getElementById('status');
                const messagesEl = document.getElementById('messages');
                
                function connect() {
                    const ws = new WebSocket("ws://localhost:8000/realtime/ws/disasters");
                    
                    ws.onopen = function() {
                        statusEl.textContent = '✅ Connected';
                        statusEl.className = 'status connected';
                    };
                    
                    ws.onmessage = function(event) {
                        const message = JSON.parse(event.data);
                        if (message.type === 'new_disaster') {
                            const data = message.data;
                            const li = document.createElement('li');
                            li.className = 'severity-' + data.severity;
                            li.innerHTML = `
                                <strong>${data.title}</strong><br>
                                <span class="meta">
                                    🏷️ ${data.disaster_type} | 
                                    ⚠️ ${data.severity} | 
                                    📍 ${data.region || 'Unknown'} | 
                                    📰 ${data.source}
                                </span>
                            `;
                            messagesEl.insertBefore(li, messagesEl.firstChild);
                        }
                    };
                    
                    ws.onclose = function() {
                        statusEl.textContent = '❌ Disconnected - Reconnecting...';
                        statusEl.className = 'status disconnected';
                        setTimeout(connect, 3000);
                    };
                    
                    ws.onerror = function(err) {
                        console.error('WebSocket error:', err);
                        ws.close();
                    };
                }
                
                connect();
            </script>
        </body>
    </html>
    """


@router.websocket("/ws/disasters")
async def realtime_disaster_feed(websocket: WebSocket):
    """
    WebSocket endpoint cho disaster feed realtime
    
    Client kết nối và nhận:
    - new_disaster: Bài báo thiên tai mới
    - heartbeat: Ping mỗi 30s để giữ connection
    """
    await websocket_service.connect(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to disaster realtime feed",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive with heartbeat
        while True:
            try:
                # Wait for client message or timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                
                # Handle client messages
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "connections": websocket_service.get_connection_count()
                })
                
    except WebSocketDisconnect:
        websocket_service.disconnect(websocket)
    except Exception as e:
        websocket_service.disconnect(websocket)


@router.get("/status")
async def get_realtime_status():
    """Lấy trạng thái WebSocket connections"""
    return {
        "status": "running",
        "active_connections": websocket_service.get_connection_count(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/recent")
async def get_recent_disasters(
    limit: int = Query(20, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168)
):
    """
    Lấy bài báo thiên tai gần đây
    
    Args:
        limit: Số lượng bài tối đa (1-100)
        hours: Trong vòng bao nhiêu giờ (1-168)
    """
    try:
        db = Database.get_db()
        collection = db["articles"]
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor = collection.find(
            {
                "is_disaster": True,
                "collected_at": {"$gte": since.isoformat()}
            },
            {
                "_id": 0,
                "title": 1,
                "source": 1,
                "url": 1,
                "disaster_type": 1,
                "severity": 1,
                "region": 1,
                "confidence": 1,
                "collected_at": 1
            }
        ).sort("collected_at", -1).limit(limit)
        
        articles = await cursor.to_list(length=limit)
        
        return {
            "count": len(articles),
            "since": since.isoformat(),
            "articles": articles
        }
        
    except Exception as e:
        return {
            "count": 0,
            "error": str(e),
            "articles": []
        }


@router.get("/stats")
async def get_realtime_stats():
    """Lấy thống kê realtime"""
    try:
        db = Database.get_db()
        collection = db["articles"]
        
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_iso = today.isoformat()
        
        # Count today's disasters (using collected_at as string comparison)
        today_count = await collection.count_documents({
            "is_disaster": True,
            "collected_at": {"$gte": today_iso}
        })
        
        # Count by severity today
        severity_counts = {}
        for severity in ["high", "medium", "low"]:
            count = await collection.count_documents({
                "is_disaster": True,
                "severity": severity,
                "collected_at": {"$gte": today_iso}
            })
            severity_counts[severity] = count
        
        # Count by type today
        type_pipeline = [
            {"$match": {"is_disaster": True, "collected_at": {"$gte": today_iso}}},
            {"$group": {"_id": "$disaster_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        cursor = collection.aggregate(type_pipeline)
        type_counts = {doc["_id"]: doc["count"] async for doc in cursor}
        
        return {
            "timestamp": now.isoformat(),
            "today_disasters": today_count,
            "by_severity": severity_counts,
            "by_type": type_counts,
            "active_connections": websocket_service.get_connection_count()
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }