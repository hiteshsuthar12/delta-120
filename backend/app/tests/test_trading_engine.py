import pytest
from app.services.trading_engine import trading_engine
from app.services.order_manager import order_manager
from app.services.position_manager import position_manager
from app.database import db_manager

@pytest.mark.asyncio
async def test_paper_trading_order_fill_and_target_exit():
    # 1. Execute entry order in paper mode
    entry_res = await order_manager.execute_entry_order(
        mode="PAPER",
        symbol="BTCUSD",
        direction="BUY",
        quantity=1.0,
        current_price=60000.0,
        target_points=1500.0,
        stop_loss_points=100.0,
        trading_day="2026-11-11",
        tick_size=0.5
    )
    assert entry_res["success"] is True
    trade_id = entry_res["trade_id"]
    pos = entry_res["position"]
    assert pos["target_price"] == 61500.0
    assert pos["stop_loss_price"] == 59900.0

    # Save position into bot state
    await db_manager.update_bot_state_fields({
        "current_position": pos,
        "state_machine_stage": "POSITION_OPEN"
    })

    # 2. Simulate price rising to Target (61500)
    bot_state = await db_manager.get_bot_state()
    exit_res = await position_manager.evaluate_open_position(
        current_price=61505.0,
        bot_state=bot_state
    )
    assert exit_res is not None
    assert exit_res["success"] is True
    assert exit_res["exit_reason"] == "TARGET"
    assert exit_res["realized_pnl"] == 1500.0  # (61500 - 60000) * 1.0

    # Verify trade in database is marked CLOSED
    saved_trade = await db_manager.get_trade(trade_id)
    assert saved_trade["status"] == "CLOSED"
    assert saved_trade["realized_pnl"] == 1500.0

    # Verify atomic lock released in bot state
    fresh_state = await db_manager.get_bot_state()
    assert fresh_state["current_position"] is None
    assert fresh_state["state_machine_stage"] == "IDLE"

@pytest.mark.asyncio
async def test_paper_trading_stop_loss_exit():
    # Execute SELL entry order
    entry_res = await order_manager.execute_entry_order(
        mode="PAPER",
        symbol="BTCUSD",
        direction="SELL",
        quantity=2.0,
        current_price=60000.0,
        target_points=1500.0,
        stop_loss_points=100.0,
        trading_day="2026-11-11",
        tick_size=0.5
    )
    pos = entry_res["position"]
    assert pos["target_price"] == 58500.0
    assert pos["stop_loss_price"] == 60100.0

    await db_manager.update_bot_state_fields({
        "current_position": pos,
        "state_machine_stage": "POSITION_OPEN"
    })

    # Simulate price rising against SELL position to Stop Loss (60100)
    bot_state = await db_manager.get_bot_state()
    exit_res = await position_manager.evaluate_open_position(
        current_price=60105.0,
        bot_state=bot_state
    )
    assert exit_res is not None
    assert exit_res["exit_reason"] == "STOP_LOSS"
    # PnL for SELL = (entry - exit) * qty = (60000 - 60100) * 2.0 = -200.0
    assert exit_res["realized_pnl"] == -200.0

@pytest.mark.asyncio
async def test_emergency_stop_flattens_and_halts():
    # Setup open position
    pos_data = {
        "trade_id": "em_test_trade",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry_price": 60000.0,
        "quantity": 1.0,
        "target_price": 61500.0,
        "stop_loss_price": 59900.0,
        "mode": "PAPER"
    }
    await db_manager.update_bot_state_fields({
        "bot_status": "RUNNING",
        "current_position": pos_data,
        "state_machine_stage": "POSITION_OPEN"
    })

    # Trigger emergency stop
    res = await trading_engine.emergency_stop()
    assert res["status"] == "EMERGENCY_STOPPED"

    # State must be flattened and locked
    state = await db_manager.get_bot_state()
    assert state["bot_status"] == "EMERGENCY_STOPPED"
    assert state["current_position"] is None

