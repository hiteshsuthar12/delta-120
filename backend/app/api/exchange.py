from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.database import db_manager
from app.schemas.exchange import ExchangeConnectRequest
from app.services.delta_exchange import delta_client
from app.utils.crypto import encrypt_secret, decrypt_secret, mask_api_key

router = APIRouter(prefix="/exchange", tags=["Exchange Settings"])

@router.post("/connect")
async def connect_exchange(payload: ExchangeConnectRequest):
    """
    Securely store Delta Exchange API credentials in encrypted form.
    Never exposes plain text secrets in database or responses.
    """
    encrypted_key = encrypt_secret(payload.api_key)
    encrypted_secret = encrypt_secret(payload.api_secret)

    cred_doc = {
        "_id": "primary_exchange",
        "encrypted_api_key": encrypted_key,
        "encrypted_api_secret": encrypted_secret,
        "environment": payload.environment,
        "updated_at": datetime.now(timezone.utc)
    }

    await db_manager.save_exchange_credentials(cred_doc)

    # Configure live client
    delta_client.set_credentials(
        api_key=payload.api_key,
        api_secret=payload.api_secret,
        environment=payload.environment
    )

    # Test connection
    is_connected = False
    try:
        balances = await delta_client.get_wallet_balances()
        is_connected = True
        await db_manager.update_bot_state_fields({"exchange_connected": True})
        await db_manager.add_log(
            event_type="EXCHANGE_CONNECTED",
            message=f"Connected to Delta Exchange ({payload.environment.upper()}). API Key: {mask_api_key(payload.api_key)}",
            severity="SUCCESS"
        )
    except Exception as e:
        await db_manager.update_bot_state_fields({"exchange_connected": False})
        await db_manager.add_log(
            event_type="API_CONNECTION_ERROR",
            message=f"Failed to verify Delta Exchange credentials: {str(e)}",
            severity="ERROR"
        )

    return {
        "success": True,
        "environment": payload.environment,
        "masked_key": mask_api_key(payload.api_key),
        "is_connected": is_connected
    }

@router.post("/test-connection")
async def test_connection():
    """Test connectivity to Delta Exchange with saved credentials."""
    creds = await db_manager.get_exchange_credentials()
    if not creds:
        return {
            "success": False,
            "message": "No API credentials configured. Please configure your Delta Exchange API credentials."
        }

    raw_key = decrypt_secret(creds.get("encrypted_api_key", ""))
    raw_secret = decrypt_secret(creds.get("encrypted_api_secret", ""))
    env = creds.get("environment", "india")

    if not raw_key or not raw_secret:
        return {"success": False, "message": "Failed to decrypt credentials or empty credentials"}

    delta_client.set_credentials(raw_key, raw_secret, env)

    try:
        balances = await delta_client.get_wallet_balances()
        total_balance = sum(float(b.get("balance", 0.0)) for b in balances if b.get("asset_symbol") in ["USDT", "USD"])
        await db_manager.update_bot_state_fields({"exchange_connected": True})
        return {
            "success": True,
            "message": f"Successfully authenticated with Delta Exchange ({env.upper()})",
            "environment": env,
            "masked_key": mask_api_key(raw_key),
            "balance_usd": round(total_balance, 2)
        }
    except Exception as e:
        await db_manager.update_bot_state_fields({"exchange_connected": False})
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "environment": env,
            "masked_key": mask_api_key(raw_key)
        }

