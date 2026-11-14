from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class StrategySettings(BaseModel):
    id: Optional[str] = Field(default="strategy_default", alias="_id")
    symbol: str = "BTCUSD"
    timeframe: str = "1h"
    ema_period: int = 120
    target_points: float = 1500.0
    stop_loss_points: float = 100.0
    max_daily_trades: int = 2
    position_size_percentage: float = 100.0  # % of available balance
    leverage: float = 25.0
    daily_reset_timezone: str = "Asia/Kolkata"
    allow_buy: bool = True
    allow_sell: bool = True
    trading_enabled: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

