import asyncio
import logging
from app.services.trading_engine import trading_engine
from app.services.delta_websocket import delta_ws_client
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class TradingWorker:
    def __init__(self):
        self._task: asyncio.Task | None = None

    def start(self):
        if self._task is None or self._task.done():
            logger.info("Spawning trading engine background worker and Delta WebSocket listener...")
            
            # Setup real-time ticker stream callback to frontend WebSocket
            def handle_ticker_update(ticker_data):
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        asyncio.create_task(websocket_manager.broadcast({
                            "type": "TICKER_FEED",
                            "ticker": ticker_data
                        }))
                except Exception:
                    pass

            delta_ws_client.on_ticker_update = handle_ticker_update

            # 1. Start Delta Exchange Public WebSocket ticker stream
            delta_ws_client.start("BTCUSD")
            
            # 2. Start trading engine monitoring loop
            self._task = asyncio.create_task(trading_engine.run_loop())

    async def stop(self):
        logger.info("Stopping trading engine background worker and Delta WebSocket listener...")
        await delta_ws_client.stop()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

trading_worker = TradingWorker()
