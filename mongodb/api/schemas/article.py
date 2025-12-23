from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ArticleBase(BaseModel):
    title: str
    summary: Optional[str] = None
    source: str
    published_at: datetime
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    region: Optional[str] = None

class ArticleCreate(ArticleBase):
    pass

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    region: Optional[str] = None

class Article(ArticleBase):
    id: str

    class Config:
        from_attributes = True

class ArticleResponse(BaseModel):
    total: int
    articles: List[Article]

class ArticleFilter(BaseModel):
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    region: Optional[str] = None
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    source: Optional[str] = None