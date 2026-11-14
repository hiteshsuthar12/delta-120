import time
import json
import hmac
import hashlib
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

BASE_URLS = {
    "india": "https://api.india.delta.exchange",
    "global": "https://api.delta.exchange",
    "testnet": "https://testnet-api.delta.exchange",
    "india_testnet": "https://cdn.india.delta.exchange",
}

class DeltaExchangeClient:
    """
    Official Delta Exchange REST API Client.
    Implements HMAC-SHA256 signature authentication, exponential backoff retries,
    order management, wallet balances, positions, and candlestick historical charts.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        environment: str = "india"
    ):
        self.api_key = api_key or settings.DELTA_API_KEY
        self.api_secret = api_secret or settings.DELTA_API_SECRET
        self.environment = environment.lower() if environment else "india"
        self.base_url = BASE_URLS.get(self.environment, BASE_URLS["india"])
        self._products_cache: Dict[str, Dict[str, Any]] = {}
        self._last_products_fetch = 0

    def set_credentials(self, api_key: str, api_secret: str, environment: str = "india"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.environment = environment.lower()
        self.base_url = BASE_URLS.get(self.environment, BASE_URLS["india"])

    def _generate_signature(self, method: str, endpoint: str, payload_str: str) -> tuple[str, str]:
        """
        Delta Exchange signature formula:
        signature_data = method.upper() + timestamp + endpoint + payload_str
        signature = hmac_sha256(secret, signature_data)
        """
        timestamp = str(int(time.time()))
        message = method.upper() + timestamp + endpoint + payload_str
        secret_bytes = bytes(self.api_secret or "", "utf-8")
        signature = hmac.new(secret_bytes, bytes(message, "utf-8"), hashlib.sha256).hexdigest()
        return signature, timestamp

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        auth_required: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        url = self.base_url + endpoint
        payload_str = json.dumps(data, separators=(',', ':')) if data else ""
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if auth_required:
            if not self.api_key or not self.api_secret:
                raise ValueError("Delta Exchange API credentials not configured.")
            sig, ts = self._generate_signature(method, endpoint, payload_str)
            headers["api-key"] = self.api_key
            headers["timestamp"] = ts
            headers["signature"] = sig

        backoff = 0.5
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, params=params, headers=headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, content=payload_str)
                    elif method.upper() == "PUT":
                        response = await client.put(url, headers=headers, content=payload_str)
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, headers=headers, content=payload_str)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    if response.status_code == 429:
                        # Rate limit handling
                        retry_after = float(response.headers.get("Retry-After", backoff))
                        logger.warning(f"Delta rate limit reached (429). Retrying after {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                        continue

                    if response.status_code >= 500:
                        logger.warning(f"Delta server error ({response.status_code}). Attempt {attempt+1}/{max_retries}")
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue

                    resp_data = response.json()
                    return resp_data
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(f"Network error contacting Delta Exchange ({url}): {exc}. Attempt {attempt+1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2

        raise RuntimeError(f"Failed to execute Delta request {method} {endpoint} after {max_retries} attempts.")

    # =========================================================================
    # Market Data
    # =========================================================================
    async def get_products(self) -> List[Dict[str, Any]]:
        """Fetch all tradable products from Delta Exchange."""
        now = time.time()
        if self._products_cache and (now - self._last_products_fetch < 300):
            return list(self._products_cache.values())

        try:
            res = await self._request("GET", "/v2/products", auth_required=False)
            products = res.get("result", [])
            self._products_cache = {p.get("symbol"): p for p in products if p.get("symbol")}
            self._last_products_fetch = now
            return products
        except Exception as e:
            logger.error(f"Failed to fetch products from Delta Exchange: {e}")
            return []

    async def get_product(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get product metadata by symbol (e.g. BTCUSD)."""
        if not self._products_cache or (time.time() - self._last_products_fetch >= 300):
            await self.get_products()
        return self._products_cache.get(symbol)

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get 24h ticker info including mark price and close price."""
        try:
            res = await self._request("GET", f"/v2/tickers/{symbol}", auth_required=False)
            return res.get("result")
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            return None

    async def get_historical_candles(
        self,
        symbol: str,
        resolution: str = "1h",
        limit: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLC historical candles.
        Delta endpoint: /v2/history/candles?resolution=1h&symbol=BTCUSD&start=...&end=...
        """
        end_time = int(time.time())
        # resolution mapping to seconds
        seconds_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "2h": 7200,
            "4h": 14400,
            "1d": 86400,
        }
        step_seconds = seconds_map.get(resolution.lower(), 3600)
        start_time = end_time - (limit * step_seconds)

        params = {
            "resolution": resolution,
            "symbol": symbol,
            "start": str(start_time),
            "end": str(end_time),
        }
        try:
            res = await self._request("GET", "/v2/history/candles", params=params, auth_required=False)
            candles = res.get("result", [])
            # Delta candles are reverse chronological (newest first). Sort ascending by time:
            candles_sorted = sorted(candles, key=lambda c: c.get("time", 0))
            return candles_sorted
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            return []

    # =========================================================================
    # Account & Positions
    # =========================================================================
    async def get_wallet_balances(self) -> List[Dict[str, Any]]:
        """Fetch user wallet balances and available margins."""
        try:
            res = await self._request("GET", "/v2/wallet/balances", auth_required=True)
            return res.get("result", [])
        except Exception as e:
            logger.error(f"Error fetching wallet balances: {e}")
            return []

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch open positions from Delta Exchange."""
        try:
            res = await self._request("GET", "/v2/positions", auth_required=True)
            return res.get("result", [])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    async def get_position_for_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        positions = await self.get_positions()
        for pos in positions:
            if pos.get("product_id") == product_id and float(pos.get("size", 0)) != 0:
                return pos
        return None

    # =========================================================================
    # Order Placement & Risk Orders
    # =========================================================================
    async def set_leverage(self, product_id: int, leverage: float) -> bool:
        """Set leverage for a given product."""
        try:
            endpoint = f"/v2/products/{product_id}/orders/leverage"
            payload = {"leverage": str(int(leverage))}
            res = await self._request("POST", endpoint, data=payload, auth_required=True)
            return res.get("success", False)
        except Exception as e:
            logger.warning(f"Could not explicitly set leverage: {e}")
            return False

    async def place_order(
        self,
        product_id: int,
        size: int,
        side: str,  # "buy" or "sell"
        order_type: str = "market_order",
        limit_price: Optional[float] = None,
        bracket_stop_loss_price: Optional[float] = None,
        bracket_take_profit_price: Optional[float] = None,
        reduce_only: bool = False,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place an order with optional bracket TP/SL on Delta Exchange.
        """
        payload: Dict[str, Any] = {
            "product_id": product_id,
            "size": size,
            "side": side.lower(),
            "order_type": order_type,
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if reduce_only:
            payload["reduce_only"] = True
        if client_order_id:
            payload["client_order_id"] = client_order_id

        # Bracket orders for native exchange TP / SL protection
        if bracket_stop_loss_price is not None:
            payload["bracket_stop_loss_price"] = str(bracket_stop_loss_price)
            payload["bracket_stop_trigger_method"] = "mark_price"
        if bracket_take_profit_price is not None:
            payload["bracket_take_profit_price"] = str(bracket_take_profit_price)

        res = await self._request("POST", "/v2/orders", data=payload, auth_required=True)
        return res

    async def place_protective_stop(
        self,
        product_id: int,
        size: int,
        side: str,  # opposite of position
        stop_price: float,
        reduce_only: bool = True
    ) -> Dict[str, Any]:
        """Place native stop market order for stop-loss protection."""
        payload = {
            "product_id": product_id,
            "size": size,
            "side": side.lower(),
            "order_type": "stop_market_order",
            "stop_price": str(stop_price),
            "reduce_only": reduce_only,
            "stop_trigger_method": "mark_price",
        }
        return await self._request("POST", "/v2/orders", data=payload, auth_required=True)

    async def place_protective_target(
        self,
        product_id: int,
        size: int,
        side: str,  # opposite of position
        limit_price: float,
        reduce_only: bool = True
    ) -> Dict[str, Any]:
        """Place native limit reduce-only order for take-profit target."""
        payload = {
            "product_id": product_id,
            "size": size,
            "side": side.lower(),
            "order_type": "limit_order",
            "limit_price": str(limit_price),
            "reduce_only": reduce_only,
        }
        return await self._request("POST", "/v2/orders", data=payload, auth_required=True)

    async def cancel_all_orders(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Cancel all open orders, optionally filtered by product_id."""
        payload = {}
        if product_id is not None:
            payload["product_id"] = product_id
        return await self._request("DELETE", "/v2/orders/all", data=payload, auth_required=True)

    async def close_position_market(self, product_id: int) -> Dict[str, Any]:
        """Emergency close position for product via market order."""
        pos = await self.get_position_for_product(product_id)
        if not pos or float(pos.get("size", 0)) == 0:
            return {"success": True, "message": "No open position to close"}
        
        size = abs(int(float(pos["size"])))
        current_side = "buy" if float(pos["size"]) > 0 else "sell"
        exit_side = "sell" if current_side == "buy" else "buy"
        
        return await self.place_order(
            product_id=product_id,
            size=size,
            side=exit_side,
            order_type="market_order",
            reduce_only=True
        )

delta_client = DeltaExchangeClient()

