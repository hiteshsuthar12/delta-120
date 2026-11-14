from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class BotStartRequest(BaseModel):
    mode: str = Field(default="PAPER", description="Trading mode: 'PAPER' or 'LIVE'")
    live_confirmation: bool = Field(default=False, description="Explicit user confirmation for LIVE real-money trading")

class BotStatusResponse(BaseModel):
    bot_status: str
    trading_mode: str
    state_machine_stage: str
    exchange_connected: bool
    current_position: Optional[Dict[str, Any]] = None
    daily_trade_count: int
    trading_day: str
    last_processed_candle: Optional[str] = None
    last_signal: Optional[Dict[str, Any]] = None
    timestamp: str

