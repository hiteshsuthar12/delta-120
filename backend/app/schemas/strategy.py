from pydantic import BaseModel, Field, field_validator
from typing import Optional

class StrategySettingsUpdate(BaseModel):
    symbol: str = Field(default="BTCUSD", description="Trading contract symbol (e.g. BTCUSD)")
    timeframe: str = Field(default="1h", description="Candle timeframe (e.g. 1h, 15m, 4h)")
    ema_period: int = Field(default=120, ge=5, le=500, description="EMA period (default: 120)")
    target_points: float = Field(default=1500.0, gt=0, description="Take profit target in price points")
    stop_loss_points: float = Field(default=100.0, gt=0, description="Stop loss in price points")
    max_daily_trades: int = Field(default=2, ge=1, le=10, description="Maximum trades per day (default: 2)")
    position_size_percentage: float = Field(default=100.0, gt=0, le=100.0, description="Position size % of available balance")
    leverage: float = Field(default=25.0, ge=1.0, le=100.0, description="Leverage multiplier (e.g. 25x)")
    daily_reset_timezone: str = Field(default="Asia/Kolkata", description="Timezone for daily reset")
    allow_buy: bool = Field(default=True, description="Enable BUY/LONG trades")
    allow_sell: bool = Field(default=True, description="Enable SELL/SHORT trades")
    trading_enabled: bool = Field(default=True, description="Global strategy enable flag")

    @field_validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("Symbol cannot be empty")
        return s

    @field_validator('timeframe')
    def validate_timeframe(cls, v: str) -> str:
        valid = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]
        if v.lower() not in valid:
            raise ValueError(f"Timeframe must be one of {valid}")
        return v.lower()

