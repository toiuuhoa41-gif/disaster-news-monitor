from pydantic import BaseModel
from typing import Optional

class Stats(BaseModel):
    total_articles: int
    disaster_articles: int
    disaster_ratio: float

class SeverityBreakdown(BaseModel):
    high: int
    medium: int
    low: int

class DisasterTypeDistribution(BaseModel):
    weather: int
    flood: int
    drought: int
    earthquake: int
    other: int

class CrawlActivityTimeline(BaseModel):
    hour: str
    articles: int