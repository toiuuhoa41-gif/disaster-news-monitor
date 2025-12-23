from pydantic import BaseModel
from typing import List, Optional

class SourceBase(BaseModel):
    name: str
    domain: str
    type: str
    is_active: bool

class SourceCreate(SourceBase):
    pass

class SourceUpdate(SourceBase):
    last_crawled: Optional[str] = None

class Source(SourceBase):
    id: str
    last_crawled: Optional[str] = None

    class Config:
        from_attributes = True

class SourceListResponse(BaseModel):
    active: int
    total: int
    sources: List[Source]