from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TradeResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    target_price: float
    stop_loss_price: float
    entry_time: datetime
    exit_time: Optional[datetime] = None
    realized_pnl: Optional[float] = 0.0
    status: str
    exchange_order_ids: List[str] = []
    exit_reason: Optional[str] = None
    trading_day: str
    mode: str

