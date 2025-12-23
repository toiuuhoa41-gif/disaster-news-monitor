from datetime import datetime, timedelta
from typing import Dict, Any, List
from mongodb.api.config.database import Database
import logging

logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self):
        pass  # Use lazy loading to avoid async issues
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def stats_collection(self):
        return self.db['stats']
    
    @property
    def articles_collection(self):
        return self.db['articles']
    
    @property
    def sources_collection(self):
        return self.db['sources']

    async def get_active_sources_count(self) -> int:
        """Get count of active sources"""
        return await self.sources_collection.count_documents({"is_active": True})

    async def get_total_sources_count(self) -> int:
        """Get total count of sources"""
        return await self.sources_collection.count_documents({})

    async def get_realtime_stats(self) -> Dict[str, Any]:
        """Get realtime stats for the dashboard"""
        total_articles = await self.articles_collection.count_documents({})
        disaster_articles = await self.articles_collection.count_documents({"is_disaster": True})
        percentage = (disaster_articles / total_articles * 100) if total_articles > 0 else 0

        # Get severity breakdown
        high = await self.articles_collection.count_documents({"severity": "high"})
        medium = await self.articles_collection.count_documents({"severity": "medium"})
        low = await self.articles_collection.count_documents({"severity": "low"})

        return {
            "total_articles": total_articles,
            "disaster_articles": disaster_articles,
            "percentage": round(percentage, 2),
            "severity": {
                "high": high,
                "medium": medium,
                "low": low
            }
        }

    async def update_daily_stats(self, total_articles: int, disaster_articles: int) -> Dict[str, Any]:
        """Update daily statistics in the database."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        stats_data = {
            "date": date_str,
            "total_articles": total_articles,
            "disaster_articles": disaster_articles,
            "disaster_ratio": (disaster_articles / total_articles * 100) if total_articles > 0 else 0
        }
        result = await self.stats_collection.update_one(
            {"date": date_str},
            {"$set": stats_data},
            upsert=True
        )
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }


class StatsUpdateService:
    """Service for updating and retrieving dashboard statistics"""
    
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def articles_collection(self):
        return self.db['articles']
    
    @property
    def stats_collection(self):
        return self.db['stats']
    
    @property
    def sources_collection(self):
        return self.db['sources']

    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get dashboard overview statistics"""
        total_articles = await self.articles_collection.count_documents({})
        disaster_articles = await self.articles_collection.count_documents({"is_disaster": True})
        disaster_ratio = round((disaster_articles / total_articles * 100), 2) if total_articles > 0 else 0

        # Get severity breakdown
        high = await self.articles_collection.count_documents({"severity": "high"})
        medium = await self.articles_collection.count_documents({"severity": "medium"})
        low = await self.articles_collection.count_documents({"severity": "low"})
        
        # Get today's articles
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today_start.isoformat()
        today_articles = await self.articles_collection.count_documents({
            "$or": [
                {"collected_at": {"$gte": today_str}},
                {"publish_date": {"$gte": today_str}}
            ]
        })
        
        # Get active sources count
        sources = await self.articles_collection.distinct("source")
        active_sources = len(sources)

        return {
            "total_articles": total_articles,
            "disaster_articles": disaster_articles,
            "disaster_ratio": disaster_ratio,
            "today_articles": today_articles,
            "active_sources": active_sources,
            "severity_high": high,
            "severity_medium": medium,
            "severity_low": low
        }

    async def get_severity_breakdown(self) -> Dict[str, int]:
        """Retrieve severity breakdown of disaster articles."""
        high = await self.articles_collection.count_documents({"severity": "high", "is_disaster": True})
        medium = await self.articles_collection.count_documents({"severity": "medium", "is_disaster": True})
        low = await self.articles_collection.count_documents({"severity": "low", "is_disaster": True})

        return {
            "high": high,
            "medium": medium,
            "low": low
        }

    async def get_disaster_type_distribution(self) -> Dict[str, int]:
        """Retrieve distribution of disaster types."""
        weather = await self.articles_collection.count_documents({"disaster_type": "weather"})
        flood = await self.articles_collection.count_documents({"disaster_type": "flood"})
        drought = await self.articles_collection.count_documents({"disaster_type": "drought"})
        earthquake = await self.articles_collection.count_documents({"disaster_type": "earthquake"})
        fire = await self.articles_collection.count_documents({"disaster_type": "fire"})
        general = await self.articles_collection.count_documents({"disaster_type": "general"})
        other = await self.articles_collection.count_documents({
            "disaster_type": {"$nin": ["weather", "flood", "drought", "earthquake", "fire", "general"]},
            "is_disaster": True
        })

        return {
            "weather": weather,
            "flood": flood,
            "drought": drought,
            "earthquake": earthquake,
            "fire": fire,
            "general": general,
            "other": other
        }

    async def get_crawl_activity_timeline(self) -> List[Dict[str, Any]]:
        """Get crawl activity timeline for the last 24 hours"""
        timeline = []
        for hour in range(0, 24, 2):
            timeline.append({
                "hour": f"{hour:02d}:00",
                "articles": 0,
                "disaster_articles": 0
            })
        return timeline

    async def update_stats(self) -> Dict[str, Any]:
        """Update all statistics"""
        overview = await self.get_dashboard_overview()
        return {
            "status": "updated",
            "overview": overview,
            "updated_at": datetime.now().isoformat()
        }