from fastapi import APIRouter, Query
from app.database import db_manager

router = APIRouter(prefix="/logs", tags=["Activity Logs"])

@router.get("")
async def get_activity_logs(limit: int = Query(50, ge=1, le=200)):
    """Retrieve recent system and trading activity logs."""
    logs = await db_manager.get_logs(limit=limit)
    return logs

