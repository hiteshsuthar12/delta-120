import pytest
from app.services.reconciliation import reconciliation_service
from app.services.delta_exchange import delta_client
from app.database import db_manager

@pytest.mark.asyncio
async def test_reconciliation_skips_in_paper_mode():
    await db_manager.update_bot_state_fields({"trading_mode": "PAPER"})
    res = await reconciliation_service.reconcile()
    assert res["status"] == "ok"
    assert res["mode"] == "PAPER"

@pytest.mark.asyncio
async def test_reconciliation_external_close_sync(monkeypatch):
    # Setup live mode with an internal open position
    pos_data = {
        "trade_id": "live_sync_trade",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry_price": 60000.0,
        "quantity": 1.0,
        "mode": "LIVE"
    }
    await db_manager.create_trade({
        "_id": "live_sync_trade",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry_price": 60000.0,
        "quantity": 1.0,
        "status": "OPEN",
        "trading_day": "2026-11-11",
        "mode": "LIVE"
    })
    await db_manager.update_bot_state_fields({
        "trading_mode": "LIVE",
        "current_position": pos_data,
        "state_machine_stage": "POSITION_OPEN"
    })

    delta_client.set_credentials("key", "secret", "india")

    # Mock Delta Exchange returning 0 positions (i.e. position was closed on exchange by TP)
    async def mock_get_positions():
        return []
    async def mock_get_product(sym):
        return {"id": 27, "symbol": "BTCUSD"}

    monkeypatch.setattr(delta_client, "get_positions", mock_get_positions)
    monkeypatch.setattr(delta_client, "get_product", mock_get_product)

    res = await reconciliation_service.reconcile()
    assert res["status"] == "reconciled"

    # Internal position should now be synchronized to None and trade CLOSED
    state = await db_manager.get_bot_state()
    assert state["current_position"] is None
    trade = await db_manager.get_trade("live_sync_trade")
    assert trade["status"] == "CLOSED"

