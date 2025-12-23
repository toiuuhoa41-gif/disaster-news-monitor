from typing import List, Dict, Any
from fastapi import HTTPException
from mongodb.api.models.source import Source
from mongodb.api.schemas.source import SourceCreate, SourceUpdate
from mongodb.api.config.database import Database
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)


# Default news sources configuration (synced with crawler)
DEFAULT_NEWS_SOURCES = [
    {
        "name": "VNExpress",
        "domain": "vnexpress.net",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 9,
        "has_native_rss": True,
        "rss_feeds": [
            "https://vnexpress.net/rss/thoi-su.rss",
            "https://vnexpress.net/rss/tin-moi-nhat.rss"
        ],
        "google_news_rss": "https://news.google.com/rss/search?q=site:vnexpress.net+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Thanh Niên",
        "domain": "thanhnien.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 8,
        "has_native_rss": True,
        "rss_feeds": ["https://thanhnien.vn/rss/home.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:thanhnien.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "VietNamNet",
        "domain": "vietnamnet.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 8,
        "has_native_rss": True,
        "rss_feeds": ["https://vietnamnet.vn/rss/thoi-su.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:vietnamnet.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Tuổi Trẻ Online",
        "domain": "tuoitre.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 8,
        "has_native_rss": True,
        "rss_feeds": ["https://tuoitre.vn/rss/thoi-su.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:tuoitre.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Người Lao Động",
        "domain": "nld.com.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 8,
        "has_native_rss": True,
        "rss_feeds": ["https://nld.com.vn/rss/home.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:nld.com.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Tin Tức",
        "domain": "baotintuc.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 7,
        "has_native_rss": True,
        "rss_feeds": ["https://baotintuc.vn/tin-moi-nhat.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:baotintuc.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Nhân Dân",
        "domain": "nhandan.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 9,
        "has_native_rss": True,
        "rss_feeds": ["https://nhandan.vn/rss/chinhtri-1171.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:nhandan.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Dân Trí",
        "domain": "dantri.com.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 8,
        "has_native_rss": True,
        "rss_feeds": ["https://dantri.com.vn/rss/xa-hoi.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:dantri.com.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "VTV",
        "domain": "vtv.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 9,
        "has_native_rss": True,
        "rss_feeds": ["https://vtv.vn/rss/xa-hoi.rss"],
        "google_news_rss": "https://news.google.com/rss/search?q=site:vtv.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "24h.com.vn",
        "domain": "24h.com.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 6,
        "has_native_rss": False,
        "rss_feeds": [],
        "google_news_rss": "https://news.google.com/rss/search?q=site:24h.com.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Mới",
        "domain": "baomoi.com",
        "type": "aggregator",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 6,
        "has_native_rss": False,
        "rss_feeds": [],
        "google_news_rss": "https://news.google.com/rss/search?q=site:baomoi.com+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Báo Chính Phủ",
        "domain": "baochinhphu.vn",
        "type": "government",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 9,
        "has_native_rss": False,
        "rss_feeds": [],
        "google_news_rss": "https://news.google.com/rss/search?q=site:baochinhphu.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Hà Nội Mới",
        "domain": "hanoimoi.com.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 7,
        "has_native_rss": False,
        "rss_feeds": [],
        "google_news_rss": "https://news.google.com/rss/search?q=site:hanoimoi.com.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    },
    {
        "name": "Tiền Phong",
        "domain": "tienphong.vn",
        "type": "news",
        "country": "Vietnam",
        "language": "vi",
        "reliability_score": 7,
        "has_native_rss": False,
        "rss_feeds": [],
        "google_news_rss": "https://news.google.com/rss/search?q=site:tienphong.vn+thiên+tai&hl=vi&gl=VN",
        "is_active": True
    }
]


class SourcesService:
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def collection(self):
        return self.db['sources']

    async def get_all_sources(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find()
        sources = await cursor.to_list(length=None)
        
        # If no sources in DB, return defaults
        if not sources:
            return DEFAULT_NEWS_SOURCES
        
        return sources

    async def get_realtime_sources(self) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"is_active": True})
        sources = await cursor.to_list(length=None)
        
        # If no sources in DB, return active defaults
        if not sources:
            return [s for s in DEFAULT_NEWS_SOURCES if s.get("is_active", True)]
        
        return sources

    async def get_source(self, source_id: str) -> Dict[str, Any]:
        source = await self.collection.find_one({"_id": source_id})
        if not source:
            # Check in defaults
            for s in DEFAULT_NEWS_SOURCES:
                if s.get("domain") == source_id:
                    return s
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    async def get_source_by_domain(self, domain: str) -> Dict[str, Any]:
        source = await self.collection.find_one({"domain": domain})
        if not source:
            for s in DEFAULT_NEWS_SOURCES:
                if s.get("domain") == domain:
                    return s
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    async def create_source(self, source_data: SourceCreate) -> Dict[str, Any]:
        data = source_data.model_dump()
        data["created_at"] = datetime.now()
        result = await self.collection.insert_one(data)
        return await self.get_source(str(result.inserted_id))

    async def update_source(self, source_id: str, source_data: SourceUpdate) -> Dict[str, Any]:
        update_data = source_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now()
        result = await self.collection.update_one(
            {"_id": source_id}, 
            {"$set": update_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Source not found")
        return await self.get_source(source_id)

    async def delete_source(self, source_id: str) -> dict:
        result = await self.collection.delete_one({"_id": source_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Source not found")
        return {"detail": "Source deleted successfully"}

    async def check_source_health(self, source_id: str) -> dict:
        source = await self.get_source(source_id)
        
        # Check RSS feed availability
        rss_status = "unknown"
        rss_feeds = source.get("rss_feeds", [])
        
        if rss_feeds:
            try:
                response = requests.head(rss_feeds[0], timeout=10)
                rss_status = "healthy" if response.status_code == 200 else "error"
            except:
                rss_status = "unreachable"
        
        return {
            "source_id": source_id,
            "domain": source.get("domain"),
            "rss_status": rss_status,
            "has_native_rss": source.get("has_native_rss", False),
            "reliability_score": source.get("reliability_score", 5),
            "status": "healthy" if rss_status == "healthy" else "warning"
        }
    
    async def init_default_sources(self) -> dict:
        """Initialize database with default sources"""
        inserted = 0
        for source in DEFAULT_NEWS_SOURCES:
            existing = await self.collection.find_one({"domain": source["domain"]})
            if not existing:
                source["created_at"] = datetime.now()
                await self.collection.insert_one(source)
                inserted += 1
        
        return {
            "message": f"Initialized {inserted} sources",
            "total_sources": len(DEFAULT_NEWS_SOURCES)
        }


class SourcesHealthService:
    """Service for checking the health of sources"""
    
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def collection(self):
        return self.db['sources']

    async def check_all_sources_health(self) -> dict:
        """Check health of all sources"""
        cursor = self.collection.find({"is_active": True})
        sources = await cursor.to_list(length=None)
        
        # If empty, count from defaults
        if not sources:
            active_count = sum(1 for s in DEFAULT_NEWS_SOURCES if s.get("is_active", True))
            total_count = len(DEFAULT_NEWS_SOURCES)
        else:
            active_count = len(sources)
            total_count = await self.collection.count_documents({})
        
        return {
            "total_sources": total_count,
            "active_sources": active_count,
            "with_native_rss": sum(1 for s in (sources or DEFAULT_NEWS_SOURCES) if s.get("has_native_rss")),
            "with_google_rss": sum(1 for s in (sources or DEFAULT_NEWS_SOURCES) if s.get("google_news_rss")),
            "status": "healthy" if active_count > 0 else "warning",
            "checked_at": datetime.now().isoformat()
        }