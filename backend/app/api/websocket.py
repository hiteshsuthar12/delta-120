import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import websocket_manager
from app.services.market_data import market_data_service
from app.database import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Real-time WebSocket endpoint for price, EMA, orders, and bot status updates."""
    await websocket_manager.connect(websocket)
    try:
        # Send initial state snapshot serialized safely with default=str
        bot_state = await db_manager.get_bot_state()
        if bot_state:
            await websocket.send_text(json.dumps({
                "type": "INITIAL_STATE",
                "state": bot_state
            }, default=str))

        # Send immediate live ticker snapshot
        live_ticker = await market_data_service.get_live_ticker("BTCUSD")
        if live_ticker:
            await websocket.send_text(json.dumps({
                "type": "TICKER_FEED",
                "ticker": live_ticker
            }, default=str))

        while True:
            # Keep connection alive and receive any client ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        websocket_manager.disconnect(websocket)


