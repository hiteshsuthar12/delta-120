import json
import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone
import websockets
from app.config import settings

logger = logging.getLogger(__name__)

WS_URLS = {
    "india": "wss://socket.india.delta.exchange",
    "global": "wss://socket.delta.exchange",
    "testnet": "wss://testnet-socket.delta.exchange",
    "india_testnet": "wss://socket.india.delta.exchange",
}

class DeltaWebSocketClient:
    """
    Official Delta Exchange Public WebSocket Client.
    Subscribes to live public market feeds (v2/ticker) with NO API keys required.
    Streams:
    - Mark Price
    - Spot / Index Price
    - Best Bid & Size
    - Best Ask & Size
    - Timestamp
    - Last Traded Price (Close)
    """
    def __init__(self, environment: str = "india"):
        self.environment = environment.lower()
        self.ws_url = WS_URLS.get(self.environment, WS_URLS["india"])
        self.is_connected: bool = False
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        
        # Real-time live market ticker snapshot
        self.market_ticker: Dict[str, Any] = {
            "symbol": "BTCUSD",
            "mark_price": 73850.0,
            "spot_price": 73890.0,
            "best_bid": 73845.0,
            "best_ask": 73845.5,
            "bid_size": 1500,
            "ask_size": 1500,
            "ltp": 73848.0,
            "timestamp": int(time.time() * 1000),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "feed_status": "CONNECTING"
        }
        
        self.on_ticker_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self._last_broadcast_time: float = 0.0

    def set_environment(self, environment: str):
        self.environment = environment.lower()
        self.ws_url = WS_URLS.get(self.environment, WS_URLS["india"])

    async def connect_and_listen(self, symbol: str = "BTCUSD"):
        """Connect to Delta Exchange Public WebSocket and stream real-time ticker data."""
        self._running = True
        backoff = 2

        while self._running:
            try:
                logger.info(f"Connecting to Delta Exchange Public WebSocket at {self.ws_url}...")
                async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=15) as ws:
                    self.is_connected = True
                    self.market_ticker["feed_status"] = "LIVE_CONNECTED"
                    backoff = 2
                    logger.info("Successfully connected to Delta Exchange Public WebSocket feed!")

                    # Subscribe to v2/ticker, l1_orderbook, and all_trades for fast 1-2s updates
                    sub_message = {
                        "type": "subscribe",
                        "payload": {
                            "channels": [
                                {
                                    "name": "v2/ticker",
                                    "symbols": [symbol]
                                },
                                {
                                    "name": "l1_orderbook",
                                    "symbols": [symbol]
                                },
                                {
                                    "name": "all_trades",
                                    "symbols": [symbol]
                                }
                            ]
                        }
                    }
                    await ws.send(json.dumps(sub_message))

                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")

                            # 1. High-frequency L1 Orderbook updates (emitted every ~100-300ms)
                            if msg_type == "l1_orderbook":
                                if "best_bid" in data and data["best_bid"]:
                                    self.market_ticker["best_bid"] = round(float(data["best_bid"]), 2)
                                if "best_ask" in data and data["best_ask"]:
                                    self.market_ticker["best_ask"] = round(float(data["best_ask"]), 2)
                                if "bid_qty" in data and data["bid_qty"]:
                                    self.market_ticker["bid_size"] = int(float(data["bid_qty"]))
                                if "ask_qty" in data and data["ask_qty"]:
                                    self.market_ticker["ask_size"] = int(float(data["ask_qty"]))
                                
                                # Use mid price as live mark reference if available
                                b_bid = self.market_ticker["best_bid"]
                                b_ask = self.market_ticker["best_ask"]
                                if b_bid and b_ask:
                                    mid_price = round((b_bid + b_ask) / 2.0, 2)
                                    self.market_ticker["mark_price"] = mid_price

                                raw_ts = data.get("timestamp") or data.get("last_updated_at")
                                if raw_ts:
                                    ts_ms = int(raw_ts / 1000) if raw_ts > 10_000_000_000_000 else int(raw_ts)
                                    self.market_ticker["timestamp"] = ts_ms
                                    self.market_ticker["timestamp_iso"] = datetime.fromtimestamp(ts_ms / 1000.0, timezone.utc).isoformat()
                                self.market_ticker["feed_status"] = "LIVE_STREAMING"

                            # 2. Real-time trade executions (emitted every ~50-200ms)
                            elif msg_type == "all_trades":
                                if "price" in data and data["price"]:
                                    self.market_ticker["ltp"] = round(float(data["price"]), 2)
                                raw_ts = data.get("timestamp")
                                if raw_ts:
                                    ts_ms = int(raw_ts / 1000) if raw_ts > 10_000_000_000_000 else int(raw_ts)
                                    self.market_ticker["timestamp"] = ts_ms
                                    self.market_ticker["timestamp_iso"] = datetime.fromtimestamp(ts_ms / 1000.0, timezone.utc).isoformat()

                            # 3. Comprehensive 24h ticker updates
                            elif msg_type == "v2/ticker" or ("mark_price" in data and "symbol" in data):
                                quotes = data.get("quotes") or {}
                                if "mark_price" in data and data["mark_price"]:
                                    self.market_ticker["mark_price"] = round(float(data["mark_price"]), 2)
                                if "spot_price" in data and data["spot_price"]:
                                    self.market_ticker["spot_price"] = round(float(data["spot_price"]), 2)
                                if "close" in data and data["close"]:
                                    self.market_ticker["ltp"] = round(float(data["close"]), 2)
                                if quotes.get("best_bid"):
                                    self.market_ticker["best_bid"] = round(float(quotes["best_bid"]), 2)
                                if quotes.get("best_ask"):
                                    self.market_ticker["best_ask"] = round(float(quotes["best_ask"]), 2)
                                if quotes.get("bid_size"):
                                    self.market_ticker["bid_size"] = int(float(quotes["bid_size"]))
                                if quotes.get("ask_size"):
                                    self.market_ticker["ask_size"] = int(float(quotes["ask_size"]))

                                raw_ts = data.get("timestamp")
                                if raw_ts:
                                    ts_ms = int(raw_ts / 1000) if raw_ts > 10_000_000_000_000 else int(raw_ts)
                                    self.market_ticker["timestamp"] = ts_ms
                                    self.market_ticker["timestamp_iso"] = datetime.fromtimestamp(ts_ms / 1000.0, timezone.utc).isoformat()
                                self.market_ticker["feed_status"] = "LIVE_STREAMING"

                            # 4. Dispatch updates to frontend every ~1.0 second
                            now_t = time.time()
                            if self.on_ticker_update and (now_t - self._last_broadcast_time >= 1.0):
                                self._last_broadcast_time = now_t
                                self.on_ticker_update(self.market_ticker)

                        except Exception as e:
                            logger.debug(f"Error parsing Delta WS message: {e}")

            except (websockets.ConnectionClosed, Exception) as exc:
                self.is_connected = False
                self.market_ticker["feed_status"] = "RECONNECTING"
                if not self._running:
                    break
                logger.warning(f"Delta WebSocket disconnected: {exc}. Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    def start(self, symbol: str = "BTCUSD"):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.connect_and_listen(symbol))

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self.is_connected = False

delta_ws_client = DeltaWebSocketClient()
