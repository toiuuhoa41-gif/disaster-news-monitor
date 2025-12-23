from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Article(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    source: str
    published_at: datetime
    disaster_type: str
    severity: str
    region: str

class ArticleCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    source: str
    published_at: datetime
    disaster_type: str
    severity: str
    region: str

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    region: Optional[str] = None

class ArticleResponse(BaseModel):
    total: int
    articles: List[Article]