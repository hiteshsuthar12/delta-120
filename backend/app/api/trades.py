from fastapi import APIRouter, Query
from typing import Optional
from app.database import db_manager
from app.utils.datetime_utils import get_current_trading_day

router = APIRouter(prefix="/trades", tags=["Trades"])

@router.get("")
async def get_trades(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g. BTCUSD)"),
    direction: Optional[str] = Query(None, description="Filter by direction (BUY/SELL)"),
    date: Optional[str] = Query(None, description="Filter by trading day (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500)
):
    """Retrieve historical trade records with filtering options."""
    trades = await db_manager.get_trades(
        symbol=symbol,
        direction=direction,
        trading_day=date,
        limit=limit
    )
    return trades

@router.get("/today")
async def get_today_trades():
    """Retrieve trades for the current trading day."""
    settings = await db_manager.get_strategy_settings() or {}
    tz = settings.get("daily_reset_timezone", "Asia/Kolkata")
    today = get_current_trading_day(tz)
    trades = await db_manager.get_trades(trading_day=today)
    return {
        "trading_day": today,
        "count": len(trades),
        "trades": trades
    }

