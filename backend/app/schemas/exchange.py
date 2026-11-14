from pydantic import BaseModel, Field
from typing import Optional

class ExchangeConnectRequest(BaseModel):
    api_key: str = Field(..., min_length=4, description="Delta Exchange API Key")
    api_secret: str = Field(..., min_length=8, description="Delta Exchange API Secret")
    environment: str = Field(default="india", description="Environment: 'india', 'global', 'testnet', 'india_testnet'")

class ExchangeTestResponse(BaseModel):
    success: bool
    message: str
    environment: str
    masked_key: str
    balance_usd: float = 0.0

