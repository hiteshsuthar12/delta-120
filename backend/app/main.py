import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import db_manager
from app.api import api_router
from app.api.websocket import router as ws_router
from app.workers.trading_worker import trading_worker
from app.services.delta_exchange import delta_client
from app.utils.crypto import decrypt_secret

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("delta_trading_bot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application Startup
    logger.info("Initializing Automated EMA 120 Trading Bot...")
    # 1. Connect MongoDB via PyMongo AsyncMongoClient
    await db_manager.connect()

    # 2. Load stored exchange credentials if available
    creds = await db_manager.get_exchange_credentials()
    if creds:
        raw_key = decrypt_secret(creds.get("encrypted_api_key", ""))
        raw_secret = decrypt_secret(creds.get("encrypted_api_secret", ""))
        env = creds.get("environment", "india")
        if raw_key and raw_secret:
            delta_client.set_credentials(raw_key, raw_secret, env)
            logger.info(f"Loaded Delta credentials for environment: {env.upper()}")

    # 3. Start independent background trading worker
    trading_worker.start()
    logger.info("Background trading worker running independently of UI.")

    yield

    # Application Shutdown
    logger.info("Shutting down trading bot services...")
    await trading_worker.stop()
    await db_manager.close()
    logger.info("Graceful shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated EMA 120 Trading Bot for Delta Exchange with Paper Trading and Strict Risk Rules",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach REST APIs & WebSocket
app.include_router(api_router)
app.include_router(ws_router)

# Mount frontend/dist for direct browser dashboard access if built
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    logger.info(f"Serving compiled React frontend dashboard from {frontend_dist}")
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "status": "online",
            "documentation": "/docs",
            "api_prefix": settings.API_V1_STR
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
