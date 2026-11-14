from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Trade(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    symbol: str = "BTCUSD"
    direction: str  # "BUY" or "SELL"
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    target_price: float
    stop_loss_price: float
    entry_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exit_time: Optional[datetime] = None
    realized_pnl: Optional[float] = 0.0
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED
    exchange_order_ids: List[str] = Field(default_factory=list)
    exit_reason: Optional[str] = None  # TARGET, STOP_LOSS, MANUAL, EMERGENCY
    trading_day: str  # YYYY-MM-DD
    mode: str = "PAPER"  # PAPER or LIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

