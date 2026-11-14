import pytest
from app.database import db_manager
from app.utils.crypto import encrypt_secret, decrypt_secret, mask_api_key

@pytest.mark.asyncio
async def test_atomic_position_lock():
    # Reset
    await db_manager.atomic_release_position_lock()

    pos1 = {"trade_id": "trade_1", "symbol": "BTCUSD"}
    pos2 = {"trade_id": "trade_2", "symbol": "BTCUSD"}

    # First acquisition succeeds
    acq1 = await db_manager.atomic_acquire_position_lock(pos1)
    assert acq1 is True

    # Concurrent second acquisition MUST FAIL!
    acq2 = await db_manager.atomic_acquire_position_lock(pos2)
    assert acq2 is False

    # After releasing lock, can acquire again
    await db_manager.atomic_release_position_lock()
    acq3 = await db_manager.atomic_acquire_position_lock(pos2)
    assert acq3 is True

@pytest.mark.asyncio
async def test_restart_recovery_from_database():
    # Setup state representing an active session before restart
    test_state = {
        "_id": "singleton",
        "bot_status": "RUNNING",
        "trading_mode": "PAPER",
        "state_machine_stage": "POSITION_OPEN",
        "current_position": {"trade_id": "retained_trade", "symbol": "BTCUSD"},
        "daily_trade_count": 2,
        "trading_day": "2026-11-11"
    }
    await db_manager.save_bot_state(test_state)

    # Simulate restart: reading state afresh
    recovered = await db_manager.get_bot_state()
    assert recovered["bot_status"] == "RUNNING"
    assert recovered["daily_trade_count"] == 2
    assert recovered["current_position"]["trade_id"] == "retained_trade"

def test_api_credential_encryption():
    secret = "my_super_secret_delta_api_key_12345"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert len(encrypted) > len(secret)

    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret

    masked = mask_api_key(secret)
    assert masked.startswith("my_s")
    assert masked.endswith("345")
    assert "secret" not in masked

