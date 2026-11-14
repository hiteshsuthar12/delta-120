from fastapi import APIRouter, HTTPException
from app.database import db_manager
from app.schemas.strategy import StrategySettingsUpdate

router = APIRouter(prefix="/strategy", tags=["Strategy Settings"])

@router.get("/settings")
async def get_strategy_settings():
    """Get active strategy settings from MongoDB."""
    settings = await db_manager.get_strategy_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Strategy settings not found")
    return settings

@router.put("/settings")
async def update_strategy_settings(payload: StrategySettingsUpdate):
    """
    Validate and update strategy configuration in MongoDB.
    """
    update_data = payload.model_dump()
    await db_manager.save_strategy_settings(update_data)
    await db_manager.add_log(
        event_type="SETTINGS_UPDATED",
        message=f"Strategy settings updated: Symbol={payload.symbol}, EMA={payload.ema_period}, TP={payload.target_points}, SL={payload.stop_loss_points}",
        severity="INFO",
        metadata=update_data
    )
    return {
        "success": True,
        "message": "Strategy settings saved successfully to MongoDB",
        "settings": update_data
    }

