import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import db_manager

@pytest.mark.asyncio
async def test_api_endpoints_end_to_end():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Health check & root access
        health_res = await ac.get("/api/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "online"

        root_res = await ac.get("/")
        assert root_res.status_code == 200

        # 2. Dashboard
        dash_res = await ac.get("/api/dashboard")
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert "account" in dash_data
        assert "bot_status" in dash_data
        assert "strategy_settings" in dash_data

        # 3. Strategy settings GET & PUT
        strat_res = await ac.get("/api/strategy/settings")
        assert strat_res.status_code == 200
        strat_data = strat_res.json()
        assert strat_data["symbol"] == "BTCUSD"

        # Update settings
        update_payload = {
            "symbol": "BTCUSD",
            "timeframe": "1h",
            "ema_period": 120,
            "target_points": 1500.0,
            "stop_loss_points": 100.0,
            "max_daily_trades": 2,
            "position_size_percentage": 100.0,
            "leverage": 25.0,
            "daily_reset_timezone": "Asia/Kolkata",
            "allow_buy": True,
            "allow_sell": True,
            "trading_enabled": True
        }
        put_res = await ac.put("/api/strategy/settings", json=update_payload)
        assert put_res.status_code == 200
        assert put_res.json()["success"] is True

        # 4. Bot Status
        status_res = await ac.get("/api/bot/status")
        assert status_res.status_code == 200
        assert "bot_status" in status_res.json()

        # 5. Start Bot (Paper mode)
        start_res = await ac.post("/api/bot/start", json={"mode": "PAPER", "live_confirmation": False})
        assert start_res.status_code == 200
        assert start_res.json()["data"]["status"] == "RUNNING"

        # 6. Stop Bot
        stop_res = await ac.post("/api/bot/stop")
        assert stop_res.status_code == 200
        assert stop_res.json()["data"]["status"] == "STOPPED"

        # 7. Emergency Stop
        em_res = await ac.post("/api/bot/emergency-stop")
        assert em_res.status_code == 200
        assert em_res.json()["data"]["status"] == "EMERGENCY_STOPPED"

        # 8. Activity Logs
        logs_res = await ac.get("/api/logs?limit=10")
        assert logs_res.status_code == 200
        assert isinstance(logs_res.json(), list)

        # 9. Trades & Today Trades
        trades_res = await ac.get("/api/trades")
        assert trades_res.status_code == 200
        assert isinstance(trades_res.json(), list)

        today_res = await ac.get("/api/trades/today")
        assert today_res.status_code == 200
        assert "trading_day" in today_res.json()

        # 10. Simulate signal endpoint (Paper mode)
        sim_res = await ac.post("/api/bot/simulate-signal", json={"direction": "BUY"})
        assert sim_res.status_code == 200
        assert sim_res.json()["success"] is True

