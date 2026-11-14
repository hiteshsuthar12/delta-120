import pytest
from app.services.risk_manager import risk_manager
from app.database import db_manager
from app.utils.datetime_utils import get_current_trading_day

def test_correct_buy_target_and_stop_loss():
    entry_price = 60000.0
    tp, sl = risk_manager.calculate_tp_sl(
        direction="BUY",
        entry_price=entry_price,
        target_points=1500.0,
        stop_loss_points=100.0,
        tick_size=0.5
    )
    assert tp == 61500.0
    assert sl == 59900.0

def test_correct_sell_target_and_stop_loss():
    entry_price = 60000.0
    tp, sl = risk_manager.calculate_tp_sl(
        direction="SELL",
        entry_price=entry_price,
        target_points=1500.0,
        stop_loss_points=100.0,
        tick_size=0.5
    )
    assert tp == 58500.0
    assert sl == 60100.0

def test_quantity_calculation():
    # Balance: $1,000, 100% position size, 25x leverage => $25,000 exposure
    # Price: $50,000 => quantity = 25,000 / 50,000 = 0.5
    qty = risk_manager.calculate_position_size(
        available_balance=1000.0,
        current_price=50000.0,
        position_size_pct=100.0,
        leverage=25.0,
        contract_value=1.0,
        min_order_qty=0.1,
        qty_step=0.1
    )
    assert qty == 0.5

def test_quantity_rejects_insufficient_balance():
    qty = risk_manager.calculate_position_size(
        available_balance=0.0,
        current_price=50000.0,
        position_size_pct=100.0,
        leverage=25.0
    )
    assert qty == 0.0

@pytest.mark.asyncio
async def test_one_open_position_rule():
    # 1. When no position is open
    can_open, msg = await risk_manager.can_open_new_position("PAPER")
    assert can_open is True

    # 2. Simulate opening a position
    pos_data = {
        "trade_id": "test_trade_1",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry_price": 60000.0,
        "quantity": 1.0,
        "target_price": 61500.0,
        "stop_loss_price": 59900.0
    }
    await db_manager.update_bot_state_fields({"current_position": pos_data})

    # 3. Must BLOCK any second position!
    can_open_second, msg = await risk_manager.can_open_new_position("PAPER")
    assert can_open_second is False
    assert "One Open Position Rule violation" in msg

@pytest.mark.asyncio
async def test_max_two_trades_per_day():
    trading_day = get_current_trading_day("Asia/Kolkata")
    # Ensure state starts with 0
    await db_manager.update_bot_state_fields({
        "current_position": None,
        "daily_trade_count": 0,
        "trading_day": trading_day
    })

    # Trade 1
    can_trade1, _ = await risk_manager.can_open_new_position("PAPER", max_daily_trades=2)
    assert can_trade1 is True
    inc1 = await db_manager.atomic_increment_daily_trades(trading_day, max_limit=2)
    assert inc1 is True

    # Trade 2
    can_trade2, _ = await risk_manager.can_open_new_position("PAPER", max_daily_trades=2)
    assert can_trade2 is True
    inc2 = await db_manager.atomic_increment_daily_trades(trading_day, max_limit=2)
    assert inc2 is True

    # Trade 3 must be BLOCKED!
    state = await db_manager.get_bot_state()
    assert state["daily_trade_count"] == 2
    can_trade3, msg = await risk_manager.can_open_new_position("PAPER", max_daily_trades=2)
    assert can_trade3 is False
    assert "Maximum daily trades limit reached" in msg

    # Incrementing beyond 2 must return False atomically
    inc3 = await db_manager.atomic_increment_daily_trades(trading_day, max_limit=2)
    assert inc3 is False

