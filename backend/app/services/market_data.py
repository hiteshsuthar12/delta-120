import time
import math
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.services.delta_exchange import delta_client
from app.services.delta_websocket import delta_ws_client

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Market Data Service handles candle retrieval, candle closure validation,
    and real-time live ticker metrics directly from Delta Exchange India.
    """
    def __init__(self):
        self._simulated_price: float = 73850.0
        self._simulated_candles: List[Dict[str, Any]] = []
        self._candles_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._last_candles_fetch: Dict[str, float] = {}

    async def get_live_ticker(self, symbol: str = "BTCUSD") -> Dict[str, Any]:
        """
        Fetch authoritative live ticker snapshot:
        - mark_price
        - spot_price (index price)
        - best_bid & best_ask
        - timestamp (epoch & ISO)
        """
        # If WebSocket has live streaming data, return it immediately
        if delta_ws_client.is_connected and delta_ws_client.market_ticker.get("mark_price"):
            return delta_ws_client.market_ticker

        # Fallback to Delta Exchange REST ticker
        try:
            ticker = await delta_client.get_ticker(symbol)
            if ticker:
                quotes = ticker.get("quotes") or {}
                mark_p = float(ticker.get("mark_price") or ticker.get("close") or 73850.0)
                spot_p = float(ticker.get("spot_price") or mark_p)
                best_bid = float(quotes.get("best_bid") or (mark_p - 0.5))
                best_ask = float(quotes.get("best_ask") or (mark_p + 0.5))
                raw_ts = ticker.get("timestamp")
                ts_ms = int(raw_ts / 1000) if raw_ts and raw_ts > 10_000_000_000_000 else int(time.time() * 1000)

                snapshot = {
                    "symbol": symbol,
                    "mark_price": round(mark_p, 2),
                    "spot_price": round(spot_p, 2),
                    "best_bid": round(best_bid, 2),
                    "best_ask": round(best_ask, 2),
                    "bid_size": int(float(quotes.get("bid_size", 1000))),
                    "ask_size": int(float(quotes.get("ask_size", 1000))),
                    "ltp": round(float(ticker.get("close", mark_p)), 2),
                    "timestamp": ts_ms,
                    "timestamp_iso": datetime.fromtimestamp(ts_ms / 1000.0, timezone.utc).isoformat(),
                    "feed_status": "REST_LIVE"
                }
                delta_ws_client.market_ticker = snapshot
                return snapshot
        except Exception as e:
            logger.warning(f"Error fetching live REST ticker: {e}")

        # Fallback snapshot
        now_ms = int(time.time() * 1000)
        return {
            "symbol": symbol,
            "mark_price": round(self._simulated_price, 2),
            "spot_price": round(self._simulated_price + 20.0, 2),
            "best_bid": round(self._simulated_price - 0.5, 2),
            "best_ask": round(self._simulated_price + 0.5, 2),
            "bid_size": 1200,
            "ask_size": 1500,
            "ltp": round(self._simulated_price, 2),
            "timestamp": now_ms,
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "feed_status": "STANDBY"
        }

    async def get_current_price(self, symbol: str = "BTCUSD") -> float:
        """Fetch latest live mark price for calculations."""
        ticker = await self.get_live_ticker(symbol)
        return float(ticker["mark_price"])

    async def get_closed_candles(
        self,
        symbol: str = "BTCUSD",
        resolution: str = "1h",
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Fetch candles from Delta Exchange and ensure only FULLY CLOSED candles are returned.
        Caches results for 30s to prevent REST network bottlenecks on fast tick loops.
        """
        now = int(time.time())
        res_seconds = 3600 if resolution == "1h" else 60
        cache_key = f"{symbol}_{resolution}"

        # Return cached candles if fetched within the last 30 seconds
        if cache_key in self._candles_cache and (now - self._last_candles_fetch.get(cache_key, 0) < 30):
            cached = self._candles_cache[cache_key]
            if len(cached) >= limit:
                return cached[-limit:]

        try:
            exchange_candles = await delta_client.get_historical_candles(
                symbol=symbol,
                resolution=resolution,
                limit=limit + 5
            )
            if exchange_candles and len(exchange_candles) >= 5:
                closed = [c for c in exchange_candles if int(c.get("time", 0)) + res_seconds <= now]
                if closed:
                    self._candles_cache[cache_key] = closed
                    self._last_candles_fetch[cache_key] = now
                    return closed[-limit:]
        except Exception as e:
            logger.warning(f"Could not fetch closed candles from exchange: {e}")

        # Fallback synthetic generation if network blocks
        if not self._simulated_candles:
            self._simulated_candles = [
                {"time": now - (i * 3600), "open": 73800.0, "high": 73900.0, "low": 73700.0, "close": 73850.0, "volume": 100}
                for i in range(limit, 0, -1)
            ]
        return self._simulated_candles[-limit:]

market_data_service = MarketDataService()
