from fastapi import APIRouter
from app.api.dashboard import router as dashboard_router
from app.api.account import router as account_router
from app.api.positions import router as positions_router
from app.api.trades import router as trades_router
from app.api.strategy import router as strategy_router
from app.api.bot import router as bot_router
from app.api.exchange import router as exchange_router
from app.api.logs import router as logs_router

api_router = APIRouter(prefix="/api")

api_router.include_router(dashboard_router)
api_router.include_router(account_router)
api_router.include_router(positions_router)
api_router.include_router(trades_router)
api_router.include_router(strategy_router)
api_router.include_router(bot_router)
api_router.include_router(exchange_router)
api_router.include_router(logs_router)

__all__ = ["api_router"]

