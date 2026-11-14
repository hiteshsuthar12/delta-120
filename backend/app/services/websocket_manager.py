import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages active WebSocket connections to frontend dashboards
    and broadcasts live market, bot, and trade updates.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast payload to all connected frontend clients."""
        if not self.active_connections:
            return
        
        # Serialize once
        serialized = json.dumps(message, default=str)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(serialized)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

websocket_manager = WebSocketManager()

