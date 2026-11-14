from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class ExchangeCredentials(BaseModel):
    id: str = Field(default="primary_exchange", alias="_id")
    encrypted_api_key: str = ""
    encrypted_api_secret: str = ""
    environment: str = "india"  # 'india', 'global', 'testnet', 'india_testnet'
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}

