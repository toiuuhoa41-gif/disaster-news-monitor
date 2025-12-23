from pydantic import BaseModel
from typing import List, Dict, Optional

class DashboardOverview(BaseModel):
    total_articles: int
    disaster_articles: int
    disaster_ratio: float
    today_articles: int = 0
    active_sources: int = 0
    severity_high: int = 0
    severity_medium: int = 0
    severity_low: int = 0

class SeverityBreakdown(BaseModel):
    high: int
    medium: int
    low: int

class DisasterTypeDistribution(BaseModel):
    weather: int = 0
    flood: int = 0
    drought: int = 0
    earthquake: int = 0
    fire: int = 0
    general: int = 0
    other: int = 0

class CrawlActivityTimeline(BaseModel):
    hour: str
    articles: int
    disaster_articles: int = 0

class CrawlTimelineResponse(BaseModel):
    timeline: List[CrawlActivityTimeline]