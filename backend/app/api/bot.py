from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
from app.database import db_manager
from app.services.trading_engine import trading_engine
from app.schemas.bot import BotStartRequest

router = APIRouter(prefix="/bot", tags=["Bot Control"])

class SimulateSignalRequest(BaseModel):
    direction: str = "BUY"  # BUY or SELL

@router.post("/start")
async def start_bot(req: BotStartRequest):
    """Start automated trading bot in PAPER or LIVE mode."""
    try:
        res = await trading_engine.start(mode=req.mode, live_confirmation=req.live_confirmation)
        return {"success": True, "data": res}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@router.post("/stop")
async def stop_bot():
    """Stop automated trading bot gracefully."""
    res = await trading_engine.stop()
    return {"success": True, "data": res}

@router.post("/emergency-stop")
async def emergency_stop():
    """
    CRITICAL: Emergency stop.
    Cancels pending orders, flattens open positions, and halts execution immediately.
    """
    res = await trading_engine.emergency_stop()
    return {"success": True, "data": res}

@router.get("/status")
async def get_bot_status():
    """Retrieve full operational state of the trading bot."""
    bot_state = await db_manager.get_bot_state() or {}
    return {
        "bot_status": bot_state.get("bot_status", "STOPPED"),
        "trading_mode": bot_state.get("trading_mode", "PAPER"),
        "state_machine_stage": bot_state.get("state_machine_stage", "IDLE"),
        "exchange_connected": bot_state.get("exchange_connected", False),
        "current_position": bot_state.get("current_position"),
        "daily_trade_count": bot_state.get("daily_trade_count", 0),
        "trading_day": bot_state.get("trading_day"),
        "last_processed_candle": bot_state.get("last_processed_candle"),
        "last_signal": bot_state.get("last_signal"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/simulate-signal")
async def simulate_signal(req: SimulateSignalRequest):
    """
    Paper Trading Testing Tool:
    Simulates an immediate EMA 120 crossover signal (BUY or SELL)
    to verify trade execution, protective orders, and risk limits on demand.
    """
    bot_state = await db_manager.get_bot_state()
    if not bot_state:
        raise HTTPException(status_code=400, detail="Bot state not initialized")
    
    if bot_state.get("trading_mode") != "PAPER":
        raise HTTPException(status_code=400, detail="Signal simulation is only available in PAPER trading mode for safety.")
    
    direction = req.direction.upper()
    if direction not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Direction must be 'BUY' or 'SELL'")

    strategy_settings = await db_manager.get_strategy_settings() or {}
    symbol = strategy_settings.get("symbol", "BTCUSD")
    current_price = 65000.0
    ema_val = 64800.0 if direction == "BUY" else 65200.0

    signal_info = {
        "symbol": symbol,
        "direction": direction,
        "candle_time": str(int(datetime.now(timezone.utc).timestamp())),
        "close_price": current_price,
        "previous_close_price": ema_val - 50 if direction == "BUY" else ema_val + 50,
        "ema_value": ema_val,
        "is_confirmed": True,
        "reason": f"Manual Paper Simulation: {direction} crossover confirmed",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    await db_manager.update_bot_state_fields({"last_signal": signal_info})
    await db_manager.add_log(
        event_type="SIMULATED_SIGNAL",
        message=f"[PAPER] Simulated {direction} signal triggered for testing.",
        severity="INFO",
        metadata=signal_info
    )

    # Force a tick cycle to process the simulated signal
    await trading_engine.tick()

    fresh_state = await db_manager.get_bot_state()
    return {
        "success": True,
        "message": f"Simulated {direction} signal triggered successfully",
        "signal": signal_info,
        "current_position": fresh_state.get("current_position"),
        "daily_trade_count": fresh_state.get("daily_trade_count")
    }
