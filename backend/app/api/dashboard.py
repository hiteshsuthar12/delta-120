from fastapi import APIRouter, Query
from datetime import datetime, timezone
import pandas as pd
from app.database import db_manager
from app.services.trading_engine import trading_engine
from app.services.market_data import market_data_service
from app.utils.datetime_utils import get_current_trading_day

router = APIRouter(prefix="", tags=["Dashboard"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "online"}

@router.get("/dashboard")
async def get_dashboard():
    """Return consolidated dashboard view."""
    account = await trading_engine.get_account_overview()
    bot_state = await db_manager.get_bot_state() or {}
    strategy_settings = await db_manager.get_strategy_settings() or {}
    today = get_current_trading_day(strategy_settings.get("daily_reset_timezone", "Asia/Kolkata"))
    recent_trades = await db_manager.get_trades(limit=10)
    recent_logs = await db_manager.get_logs(limit=25)
    live_ticker = await market_data_service.get_live_ticker(strategy_settings.get("symbol", "BTCUSD"))

    return {
        "account": account,
        "bot_status": bot_state.get("bot_status", "STOPPED"),
        "trading_mode": bot_state.get("trading_mode", "PAPER"),
        "state_machine_stage": bot_state.get("state_machine_stage", "IDLE"),
        "exchange_connected": bot_state.get("exchange_connected", False),
        "current_position": bot_state.get("current_position"),
        "daily_trade_count": bot_state.get("daily_trade_count", 0),
        "trading_day": today,
        "last_signal": bot_state.get("last_signal"),
        "strategy_settings": strategy_settings,
        "recent_trades": recent_trades,
        "recent_logs": recent_logs,
        "live_ticker": live_ticker,
        "server_time": datetime.now(timezone.utc).isoformat()
    }

@router.get("/market/ticker")
async def get_market_ticker(symbol: str = Query("BTCUSD")):
    """
    Live Public Delta Exchange India Market Feed:
    Returns mark price, spot/index price, best bid, best ask, and timestamp.
    No authentication required.
    """
    ticker = await market_data_service.get_live_ticker(symbol)
    return ticker

@router.get("/chart/candles")
async def get_chart_candles(
    symbol: str = Query("BTCUSD"),
    resolution: str = Query("1h"),
    limit: int = Query(250, ge=20, le=1000)
):
    """
    Fetch OHLC candlestick data with pre-calculated EMA 120 overlay
    for TradingView Lightweight Charts rendering.
    """
    candles = await market_data_service.get_closed_candles(
        symbol=symbol,
        resolution=resolution,
        limit=limit
    )
    current_price = await market_data_service.get_current_price(symbol)
    
    tv_candles = []
    tv_ema = []
    
    if candles and len(candles) >= 5:
        df = pd.DataFrame(candles)
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Calculate EMA 120 over historical closes
        period = 120 if len(df) >= 120 else min(len(df), 20)
        df["ema"] = df["close"].ewm(span=period, adjust=False).mean()
        df = df.sort_values(by="time", ascending=True)
        
        # Eliminate duplicate timestamps if any
        df = df.drop_duplicates(subset=["time"])
        
        for _, row in df.iterrows():
            t = int(row["time"])
            o = round(float(row["open"]), 2)
            h = round(float(row["high"]), 2)
            l = round(float(row["low"]), 2)
            c = round(float(row["close"]), 2)
            tv_candles.append({
                "time": t,
                "open": o,
                "high": h,
                "low": l,
                "close": c
            })
            if pd.notna(row["ema"]):
                tv_ema.append({
                    "time": t,
                    "value": round(float(row["ema"]), 2)
                })

    latest_ema = tv_ema[-1]["value"] if tv_ema else current_price

    return {
        "symbol": symbol,
        "resolution": resolution,
        "current_price": current_price,
        "latest_ema": latest_ema,
        "candles": tv_candles,
        "ema": tv_ema
    }
