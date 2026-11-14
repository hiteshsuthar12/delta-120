import os
import sys
from pathlib import Path
import pytest
import asyncio

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import db_manager
from app.config import settings

@pytest.fixture(autouse=True)
async def setup_test_db():
    # Force fallback/memory store mode for isolated fast unit tests
    db_manager._fallback_mode = True
    db_manager._memory_store = {
        "users": {},
        "exchange_credentials": {},
        "strategy_settings": {},
        "trades": {},
        "bot_state": {},
        "activity_logs": {},
    }
    await db_manager.init_default_data()
    yield

