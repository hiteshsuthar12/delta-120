from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AccountOverview(BaseModel):
    total_balance: float
    available_balance: float
    used_margin: float
    today_realized_pnl: float
    today_unrealized_pnl: float
    today_trades_count: int
    winning_trades: int
    losing_trades: int

class DashboardDataResponse(BaseModel):
    account: AccountOverview
    bot_status: str
    trading_mode: str
    state_machine_stage: str
    exchange_connected: bool
    current_position: Optional[Dict[str, Any]] = None
    last_signal: Optional[Dict[str, Any]] = None
    strategy_settings: Dict[str, Any]
    recent_trades: List[Dict[str, Any]]
    recent_logs: List[Dict[str, Any]]
    server_time: str

