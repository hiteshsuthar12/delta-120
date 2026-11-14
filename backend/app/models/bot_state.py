from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class BotPosition(BaseModel):
    trade_id: str
    symbol: str
    direction: str  # "BUY" or "SELL" (LONG or SHORT)
    entry_price: float
    current_price: float
    target_price: float
    stop_loss_price: float
    quantity: float
    unrealized_pnl: float = 0.0
    status: str = "OPEN"
    mode: str = "PAPER"
    entry_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SignalInfo(BaseModel):
    symbol: str
    direction: str  # "BUY" or "SELL"
    candle_time: str
    close_price: float
    previous_close_price: float
    ema_value: float
    is_confirmed: bool = True
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BotState(BaseModel):
    id: str = Field(default="singleton", alias="_id")
    bot_status: str = "STOPPED"  # RUNNING, STOPPED, EMERGENCY_STOPPED
    trading_mode: str = "PAPER"  # PAPER or LIVE
    state_machine_stage: str = "IDLE"  # IDLE, SIGNAL_DETECTED, ENTRY_PENDING, POSITION_OPEN, EXIT_PENDING, PARTIALLY_FILLED, ORDER_REJECTED, PROTECTION_PENDING, EMERGENCY_EXIT, EXCHANGE_DISCONNECTED
    current_position: Optional[BotPosition] = None
    daily_trade_count: int = 0
    trading_day: str = ""
    last_processed_candle: Optional[str] = None
    last_signal: Optional[SignalInfo] = None
    exchange_connected: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

