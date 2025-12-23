"""
Crawl Router - API endpoints cho việc thu thập tin tức

Endpoints:
- POST /crawl/google-news - Crawl từ Google News RSS
- POST /crawl/direct-sources - Crawl từ RSS trực tiếp
- POST /crawl/all - Crawl từ tất cả nguồn
- GET /crawl/sources - Danh sách nguồn RSS
- GET /crawl/status - Trạng thái crawl gần nhất
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from mongodb.api.services.crawl_service import (
    CrawlService, 
    DailyCrawlService,
    DIRECT_RSS_SOURCES,
    DISASTER_SEARCH_KEYWORDS
)
from mongodb.api.config.database import Database

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crawl", tags=["crawl"])

# Store crawl status in memory
_crawl_status = {
    "is_running": False,
    "last_run": None,
    "last_result": None
}


# =====================================================
# SCHEMAS
# =====================================================

class CrawlResponse(BaseModel):
    success: bool
    message: str
    started_at: str
    task_id: Optional[str] = None


class CrawlStatsResponse(BaseModel):
    is_running: bool
    last_run: Optional[str]
    last_result: Optional[Dict[str, Any]]


class SourceInfo(BaseModel):
    key: str
    name: str
    domain: str
    rss_count: int


class SourcesResponse(BaseModel):
    direct_sources: List[SourceInfo]
    google_news_keywords: List[str]


# =====================================================
# BACKGROUND TASKS
# =====================================================

async def _run_google_news_crawl(max_keywords: int = 5):
    """Background task for Google News crawl"""
    global _crawl_status
    _crawl_status["is_running"] = True
    _crawl_status["last_run"] = datetime.now().isoformat()
    
    try:
        service = CrawlService()
        result = await service.crawl_google_news(max_keywords=max_keywords)
        _crawl_status["last_result"] = {
            "type": "google_news",
            **result,
            "completed_at": datetime.now().isoformat()
        }
        logger.info(f"Google News crawl completed: {result}")
    except Exception as e:
        _crawl_status["last_result"] = {
            "type": "google_news",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        logger.error(f"Google News crawl failed: {e}")
    finally:
        _crawl_status["is_running"] = False


async def _run_direct_sources_crawl(sources: Optional[List[str]] = None):
    """Background task for direct sources crawl"""
    global _crawl_status
    _crawl_status["is_running"] = True
    _crawl_status["last_run"] = datetime.now().isoformat()
    
    try:
        service = CrawlService()
        result = await service.crawl_direct_sources(sources=sources)
        _crawl_status["last_result"] = {
            "type": "direct_sources",
            "sources": sources or list(DIRECT_RSS_SOURCES.keys()),
            **result,
            "completed_at": datetime.now().isoformat()
        }
        logger.info(f"Direct sources crawl completed: {result}")
    except Exception as e:
        _crawl_status["last_result"] = {
            "type": "direct_sources",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        logger.error(f"Direct sources crawl failed: {e}")
    finally:
        _crawl_status["is_running"] = False


async def _run_full_crawl():
    """Background task for full crawl"""
    global _crawl_status
    _crawl_status["is_running"] = True
    _crawl_status["last_run"] = datetime.now().isoformat()
    
    try:
        service = CrawlService()
        result = await service.crawl_all()
        _crawl_status["last_result"] = {
            "type": "full_crawl",
            **result,
            "completed_at": datetime.now().isoformat()
        }
        logger.info(f"Full crawl completed: {result}")
    except Exception as e:
        _crawl_status["last_result"] = {
            "type": "full_crawl",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        }
        logger.error(f"Full crawl failed: {e}")
    finally:
        _crawl_status["is_running"] = False


# =====================================================
# ENDPOINTS
# =====================================================

@router.get("/sources", response_model=SourcesResponse)
async def get_sources():
    """
    Lấy danh sách tất cả nguồn RSS và từ khóa tìm kiếm
    """
    direct_sources = [
        SourceInfo(
            key=key,
            name=config["name"],
            domain=config["domain"],
            rss_count=len(config["rss_urls"])
        )
        for key, config in DIRECT_RSS_SOURCES.items()
    ]
    
    return SourcesResponse(
        direct_sources=direct_sources,
        google_news_keywords=DISASTER_SEARCH_KEYWORDS
    )


@router.get("/status", response_model=CrawlStatsResponse)
async def get_status():
    """
    Lấy trạng thái crawl hiện tại
    """
    return CrawlStatsResponse(
        is_running=_crawl_status["is_running"],
        last_run=_crawl_status["last_run"],
        last_result=_crawl_status["last_result"]
    )


@router.post("/google-news", response_model=CrawlResponse)
async def crawl_google_news(
    background_tasks: BackgroundTasks,
    max_keywords: int = 5
):
    """
    Bắt đầu crawl từ Google News RSS
    
    - **max_keywords**: Số từ khóa tối đa để tìm kiếm (mặc định: 5)
    """
    if _crawl_status["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Crawl đang chạy. Vui lòng đợi hoàn thành."
        )
    
    background_tasks.add_task(_run_google_news_crawl, max_keywords)
    
    return CrawlResponse(
        success=True,
        message=f"Đã bắt đầu crawl Google News với {max_keywords} từ khóa",
        started_at=datetime.now().isoformat()
    )


@router.post("/direct-sources", response_model=CrawlResponse)
async def crawl_direct_sources(
    background_tasks: BackgroundTasks,
    sources: Optional[List[str]] = None
):
    """
    Bắt đầu crawl từ RSS trực tiếp
    
    - **sources**: Danh sách key nguồn (nếu None, crawl tất cả)
    """
    if _crawl_status["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Crawl đang chạy. Vui lòng đợi hoàn thành."
        )
    
    # Validate sources
    if sources:
        invalid = [s for s in sources if s not in DIRECT_RSS_SOURCES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Nguồn không hợp lệ: {invalid}. Nguồn hợp lệ: {list(DIRECT_RSS_SOURCES.keys())}"
            )
    
    background_tasks.add_task(_run_direct_sources_crawl, sources)
    
    source_count = len(sources) if sources else len(DIRECT_RSS_SOURCES)
    return CrawlResponse(
        success=True,
        message=f"Đã bắt đầu crawl từ {source_count} nguồn RSS",
        started_at=datetime.now().isoformat()
    )


@router.post("/all", response_model=CrawlResponse)
async def crawl_all(background_tasks: BackgroundTasks):
    """
    Bắt đầu crawl từ TẤT CẢ nguồn (Google News + Direct RSS)
    
    Đây là full crawl, có thể mất 5-10 phút.
    """
    if _crawl_status["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Crawl đang chạy. Vui lòng đợi hoàn thành."
        )
    
    background_tasks.add_task(_run_full_crawl)
    
    return CrawlResponse(
        success=True,
        message="Đã bắt đầu full crawl từ tất cả nguồn",
        started_at=datetime.now().isoformat()
    )


@router.get("/logs")
async def get_crawl_logs(limit: int = 10):
    """
    Lấy lịch sử các lần crawl gần đây
    """
    try:
        db = Database.get_db()
        cursor = db['crawl_logs'].find().sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for log in logs:
            log['_id'] = str(log['_id'])
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].isoformat() if hasattr(log['timestamp'], 'isoformat') else str(log['timestamp'])
        
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error fetching crawl logs: {e}")
        return {"logs": [], "count": 0, "error": str(e)}


@router.post("/test")
async def test_crawl():
    """
    Test crawl nhanh - chỉ fetch 1 keyword và 1 source
    Không lưu vào database
    """
    service = CrawlService()
    
    try:
        # Test Google News
        google_articles = await service.fetch_google_news_rss("bão Việt Nam")
        
        # Test direct source
        direct_articles = await service.fetch_direct_rss("vnexpress")
        
        await service.close()
        
        return {
            "success": True,
            "google_news": {
                "keyword": "bão Việt Nam",
                "count": len(google_articles),
                "sample": google_articles[0].title if google_articles else None
            },
            "direct_source": {
                "source": "vnexpress",
                "count": len(direct_articles),
                "sample": direct_articles[0].title if direct_articles else None
            }
        }
    except Exception as e:
        await service.close()
        return {
            "success": False,
            "error": str(e)
        }
