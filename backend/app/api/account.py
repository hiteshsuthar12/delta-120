from fastapi import APIRouter
from app.services.trading_engine import trading_engine

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/balance")
async def get_balance():
    """Retrieve current account balances and margin utilization."""
    overview = await trading_engine.get_account_overview()
    return overview

