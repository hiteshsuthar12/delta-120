import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "Automated EMA 120 Trading Bot"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    
    # MongoDB
    MONGODB_URI: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    MONGODB_DATABASE: str = Field(default="ema_trading_bot", alias="MONGODB_DATABASE")
    
    # Encryption for Exchange Credentials
    ENCRYPTION_KEY: str = Field(default="D3lt4Em4Tr4d1ngB0tS3cr3tK3y1234567890123456=", alias="ENCRYPTION_KEY")
    
    # Delta Exchange Default Configuration
    DELTA_ENVIRONMENT: str = "india"  # 'india', 'global', 'testnet', 'india_testnet'
    DELTA_API_KEY: str = ""
    DELTA_API_SECRET: str = ""
    
    # Trading Defaults
    DEFAULT_SYMBOL: str = "BTCUSD"
    DEFAULT_TIMEFRAME: str = "1h"
    DEFAULT_EMA_PERIOD: int = 120
    DEFAULT_TARGET_POINTS: float = 1500.0
    DEFAULT_STOP_LOSS_POINTS: float = 100.0
    DEFAULT_MAX_DAILY_TRADES: int = 2
    DEFAULT_POSITION_SIZE_PCT: float = 100.0
    DEFAULT_LEVERAGE: float = 25.0
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"
    DEFAULT_TRADING_MODE: str = "PAPER"  # PAPER or LIVE
    
    # Engine Settings
    ENGINE_INTERVAL_SECONDS: int = 15
    RECONCILIATION_INTERVAL_SECONDS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
