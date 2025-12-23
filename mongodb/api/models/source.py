from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Source(BaseModel):
    id: Optional[str] = None
    name: str
    domain: str
    type: str
    is_active: bool
    last_crawled: Optional[datetime] = None

    class Config:
        from_attributes = True