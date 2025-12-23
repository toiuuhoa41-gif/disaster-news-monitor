from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SystemStatus(BaseModel):
    system_status: str
    realtime_ingestion: bool
    active_sources: int
    total_sources: int
    version: str
    server_time: datetime

class RealtimeStats(BaseModel):
    total_articles: int
    disaster_articles: int
    percentage: float
    severity: dict  # This can be further defined as a separate model if needed.