from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ActivityLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str  # BOT_STARTED, BOT_STOPPED, EMA_CROSSOVER, BUY_ORDER, SELL_ORDER, TARGET_REACHED, STOP_LOSS_TRIGGERED, DAILY_LIMIT_REACHED, API_ERROR, EMERGENCY_STOP
    message: str
    severity: str = "INFO"  # INFO, WARNING, ERROR, SUCCESS, CRITICAL
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

