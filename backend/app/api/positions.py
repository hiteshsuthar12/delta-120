from fastapi import APIRouter
from app.database import db_manager

router = APIRouter(prefix="/positions", tags=["Positions"])

@router.get("")
async def get_positions():
    """Retrieve currently active position."""
    bot_state = await db_manager.get_bot_state()
    pos = bot_state.get("current_position") if bot_state else None
    return {
        "has_open_position": pos is not None,
        "position": pos
    }

