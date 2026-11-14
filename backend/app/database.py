import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pymongo import AsyncMongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)

class MongoDatabaseManager:
    """
    MongoDB Connection Manager using official PyMongo Async API (AsyncMongoClient).
    Manages client lifecycle, database references, indexes, and atomic state operations.
    """
    def __init__(self):
        
        self.client: Optional[AsyncMongoClient] = None
        self.db = None
        self.is_connected: bool = False
        self._fallback_mode: bool = False
        self._memory_store: Dict[str, Dict[str, Any]] = {
            "users": {},
            "exchange_credentials": {},
            "strategy_settings": {},
            "trades": {},
            "bot_state": {},
            "activity_logs": {},
        }

    async def connect(self):
        """Establish connection to MongoDB using AsyncMongoClient."""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI} (database: {settings.MONGODB_DATABASE})...")
            self.client = AsyncMongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2500,
                connectTimeoutMS=2500,
            )
            self.db = self.client[settings.MONGODB_DATABASE]
            # Verify connectivity via ping
            await self.client.admin.command('ping')
            self.is_connected = True
            self._fallback_mode = False
            logger.info("Successfully connected to MongoDB cluster!")
            await self.init_indexes()
            await self.init_default_data()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
            logger.warning(
                f"Could not connect to MongoDB server: {exc}. "
                "Operating with resilient asynchronous in-memory data store for testing/offline mode."
            )
            self.is_connected = False
            self._fallback_mode = True
            await self.init_default_data()

    async def close(self):
        """Gracefully close MongoDB client."""
        if self.client:
            logger.info("Closing MongoDB client...")
            try:
                await self.client.close()
            except Exception as e:
                logger.error(f"Error while closing MongoDB client: {e}")
            self.is_connected = False

    async def init_indexes(self):
        """Create required indexes as per requirements."""
        if not self.is_connected or self._fallback_mode:
            return
        try:
            # users.username (unique)
            await self.db.users.create_index([("username", ASCENDING)], unique=True)
            
            # trades indexes
            await self.db.trades.create_index([("entry_time", DESCENDING)])
            await self.db.trades.create_index([("status", ASCENDING)])
            await self.db.trades.create_index([("symbol", ASCENDING)])
            await self.db.trades.create_index([("trading_day", ASCENDING)])
            
            # activity_logs.timestamp
            await self.db.activity_logs.create_index([("timestamp", DESCENDING)])
            
            # strategy_settings.symbol
            await self.db.strategy_settings.create_index([("symbol", ASCENDING)])
            
            logger.info("MongoDB indexes verified and created successfully.")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def init_default_data(self):
        """Seed initial strategy settings and singleton bot state if empty."""
        try:
            # Default strategy settings
            settings_doc = await self.get_strategy_settings()
            if not settings_doc:
                default_settings = {
                    "_id": "strategy_default",
                    "symbol": settings.DEFAULT_SYMBOL,
                    "timeframe": settings.DEFAULT_TIMEFRAME,
                    "ema_period": settings.DEFAULT_EMA_PERIOD,
                    "target_points": settings.DEFAULT_TARGET_POINTS,
                    "stop_loss_points": settings.DEFAULT_STOP_LOSS_POINTS,
                    "max_daily_trades": settings.DEFAULT_MAX_DAILY_TRADES,
                    "position_size_percentage": settings.DEFAULT_POSITION_SIZE_PCT,
                    "leverage": settings.DEFAULT_LEVERAGE,
                    "daily_reset_timezone": settings.DEFAULT_TIMEZONE,
                    "allow_buy": True,
                    "allow_sell": True,
                    "trading_enabled": True,
                    "updated_at": datetime.now(timezone.utc),
                }
                await self.save_strategy_settings(default_settings)

            # Default singleton bot state
            bot_state = await self.get_bot_state()
            if not bot_state:
                from app.utils.datetime_utils import get_current_trading_day
                initial_state = {
                    "_id": "singleton",
                    "bot_status": "STOPPED",
                    "trading_mode": settings.DEFAULT_TRADING_MODE,
                    "state_machine_stage": "IDLE",
                    "current_position": None,
                    "daily_trade_count": 0,
                    "trading_day": get_current_trading_day(settings.DEFAULT_TIMEZONE),
                    "last_processed_candle": None,
                    "last_signal": None,
                    "exchange_connected": False,
                    "updated_at": datetime.now(timezone.utc),
                }
                await self.save_bot_state(initial_state)
        except Exception as e:
            logger.error(f"Error seeding initial data: {e}")

    # =========================================================================
    # Strategy Settings Operations
    # =========================================================================
    async def get_strategy_settings(self) -> Optional[Dict[str, Any]]:
        if self.is_connected and not self._fallback_mode:
            return await self.db.strategy_settings.find_one({"_id": "strategy_default"})
        return self._memory_store["strategy_settings"].get("strategy_default")

    async def save_strategy_settings(self, doc: Dict[str, Any]) -> bool:
        doc["_id"] = "strategy_default"
        doc["updated_at"] = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.strategy_settings.update_one(
                {"_id": "strategy_default"},
                {"$set": doc},
                upsert=True
            )
            return True
        self._memory_store["strategy_settings"]["strategy_default"] = doc
        return True

    # =========================================================================
    # Bot State Operations (Singleton + Atomic Locks)
    # =========================================================================
    async def get_bot_state(self) -> Optional[Dict[str, Any]]:
        if self.is_connected and not self._fallback_mode:
            return await self.db.bot_state.find_one({"_id": "singleton"})
        return self._memory_store["bot_state"].get("singleton")

    async def save_bot_state(self, state: Dict[str, Any]) -> bool:
        state["_id"] = "singleton"
        state["updated_at"] = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.bot_state.update_one(
                {"_id": "singleton"},
                {"$set": state},
                upsert=True
            )
            return True
        self._memory_store["bot_state"]["singleton"] = state
        return True

    async def update_bot_state_fields(self, update_fields: Dict[str, Any]) -> bool:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.bot_state.update_one(
                {"_id": "singleton"},
                {"$set": update_fields},
                upsert=True
            )
            return True
        if "singleton" not in self._memory_store["bot_state"]:
            self._memory_store["bot_state"]["singleton"] = {"_id": "singleton"}
        self._memory_store["bot_state"]["singleton"].update(update_fields)
        return True

    async def atomic_acquire_position_lock(self, position_data: Dict[str, Any]) -> bool:
        """
        ATOMIC ONE OPEN POSITION RULE:
        Acquire entry lock only if current_position is null.
        Guarantees that two concurrent signals cannot simultaneously open a trade.
        """
        now = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            result = await self.db.bot_state.find_one_and_update(
                {
                    "_id": "singleton",
                    "current_position": None,
                    "state_machine_stage": {"$in": ["IDLE", "SIGNAL_DETECTED"]}
                },
                {
                    "$set": {
                        "current_position": position_data,
                        "state_machine_stage": "ENTRY_PENDING",
                        "updated_at": now
                    }
                }
            )
            return result is not None

        # Fallback memory store implementation with atomic check
        state = self._memory_store["bot_state"].get("singleton", {})
        if state.get("current_position") is None and state.get("state_machine_stage") in ["IDLE", "SIGNAL_DETECTED"]:
            state["current_position"] = position_data
            state["state_machine_stage"] = "ENTRY_PENDING"
            state["updated_at"] = now
            return True
        return False

    async def atomic_release_position_lock(self) -> bool:
        """Clear current position atomically once closed and confirmed by exchange."""
        now = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.bot_state.update_one(
                {"_id": "singleton"},
                {
                    "$set": {
                        "current_position": None,
                        "state_machine_stage": "IDLE",
                        "updated_at": now
                    }
                }
            )
            return True
        state = self._memory_store["bot_state"].get("singleton", {})
        state["current_position"] = None
        state["state_machine_stage"] = "IDLE"
        state["updated_at"] = now
        return True

    async def atomic_increment_daily_trades(self, trading_day: str, max_limit: int) -> bool:
        """
        ATOMIC MAXIMUM TWO TRADES PER DAY ENFORCEMENT:
        If trading_day is different, resets count to 1.
        If trading_day is the same, increments ONLY IF current count < max_limit.
        Returns True if increment succeeded, False if limit reached.
        """
        now = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            # Case 1: New trading day reset to 1
            reset_result = await self.db.bot_state.find_one_and_update(
                {
                    "_id": "singleton",
                    "trading_day": {"$ne": trading_day}
                },
                {
                    "$set": {
                        "trading_day": trading_day,
                        "daily_trade_count": 1,
                        "updated_at": now
                    }
                }
            )
            if reset_result is not None:
                return True

            # Case 2: Same trading day, increment if < max_limit
            inc_result = await self.db.bot_state.find_one_and_update(
                {
                    "_id": "singleton",
                    "trading_day": trading_day,
                    "daily_trade_count": {"$lt": max_limit}
                },
                {
                    "$inc": {"daily_trade_count": 1},
                    "$set": {"updated_at": now}
                }
            )
            return inc_result is not None

        # Fallback memory store implementation
        state = self._memory_store["bot_state"].get("singleton", {})
        current_day = state.get("trading_day")
        if current_day != trading_day:
            state["trading_day"] = trading_day
            state["daily_trade_count"] = 1
            state["updated_at"] = now
            return True
        count = state.get("daily_trade_count", 0)
        if count < max_limit:
            state["daily_trade_count"] = count + 1
            state["updated_at"] = now
            return True
        return False

    # =========================================================================
    # Trades Operations
    # =========================================================================
    async def create_trade(self, trade_doc: Dict[str, Any]) -> str:
        import uuid
        if "_id" not in trade_doc or not trade_doc["_id"]:
            trade_doc["_id"] = str(uuid.uuid4())
        trade_doc["created_at"] = trade_doc.get("created_at", datetime.now(timezone.utc))
        trade_doc["updated_at"] = datetime.now(timezone.utc)

        if self.is_connected and not self._fallback_mode:
            await self.db.trades.insert_one(trade_doc)
            return str(trade_doc["_id"])

        self._memory_store["trades"][trade_doc["_id"]] = trade_doc
        return str(trade_doc["_id"])

    async def update_trade(self, trade_id: str, update_fields: Dict[str, Any]) -> bool:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.trades.update_one(
                {"_id": trade_id},
                {"$set": update_fields}
            )
            return True
        if trade_id in self._memory_store["trades"]:
            self._memory_store["trades"][trade_id].update(update_fields)
            return True
        return False

    async def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and not self._fallback_mode:
            return await self.db.trades.find_one({"_id": trade_id})
        return self._memory_store["trades"].get(trade_id)

    async def get_trades(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        trading_day: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if symbol:
            query["symbol"] = symbol
        if direction:
            query["direction"] = direction.upper()
        if trading_day:
            query["trading_day"] = trading_day

        if self.is_connected and not self._fallback_mode:
            cursor = self.db.trades.find(query).sort("entry_time", DESCENDING).limit(limit)
            return [doc async for doc in cursor]

        # Memory store query
        trades = list(self._memory_store["trades"].values())
        filtered = []
        for t in trades:
            if symbol and t.get("symbol") != symbol:
                continue
            if direction and t.get("direction") != direction.upper():
                continue
            if trading_day and t.get("trading_day") != trading_day:
                continue
            filtered.append(t)
        filtered.sort(key=lambda x: str(x.get("entry_time", "")), reverse=True)
        return filtered[:limit]

    # =========================================================================
    # Activity Logs Operations
    # =========================================================================
    async def add_log(
        self,
        event_type: str,
        message: str,
        severity: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        import uuid
        log_doc = {
            "_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "event_type": event_type,
            "message": message,
            "severity": severity,
            "metadata": metadata or {}
        }
        if self.is_connected and not self._fallback_mode:
            try:
                await self.db.activity_logs.insert_one(log_doc)
            except Exception as e:
                logger.error(f"Failed to insert activity log: {e}")
        else:
            self._memory_store["activity_logs"][log_doc["_id"]] = log_doc
            # keep max 500 logs in memory
            if len(self._memory_store["activity_logs"]) > 500:
                oldest = sorted(self._memory_store["activity_logs"].keys())[0]
                del self._memory_store["activity_logs"][oldest]
        return log_doc

    async def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        if self.is_connected and not self._fallback_mode:
            cursor = self.db.activity_logs.find().sort("timestamp", DESCENDING).limit(limit)
            return [doc async for doc in cursor]
        logs = list(self._memory_store["activity_logs"].values())
        logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return logs[:limit]

    # =========================================================================
    # Exchange Credentials Operations (Encrypted)
    # =========================================================================
    async def get_exchange_credentials(self) -> Optional[Dict[str, Any]]:
        if self.is_connected and not self._fallback_mode:
            return await self.db.exchange_credentials.find_one({"_id": "primary_exchange"})
        return self._memory_store["exchange_credentials"].get("primary_exchange")

    async def save_exchange_credentials(self, doc: Dict[str, Any]) -> bool:
        doc["_id"] = "primary_exchange"
        doc["updated_at"] = datetime.now(timezone.utc)
        if self.is_connected and not self._fallback_mode:
            await self.db.exchange_credentials.update_one(
                {"_id": "primary_exchange"},
                {"$set": doc},
                upsert=True
            )
            return True
        self._memory_store["exchange_credentials"]["primary_exchange"] = doc
        return True

db_manager = MongoDatabaseManager()
