"""
Internal Router - Endpoints nội bộ cho Crawler

Endpoints:
- POST /internal/crawl - Trigger crawl thủ công
- POST /internal/classify - Phân loại bài báo
- POST /internal/ingest - Nhập bài báo vào pipeline
- POST /internal/ingest/batch - Nhập batch bài báo
- GET /internal/pipeline/stats - Thống kê pipeline
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from mongodb.api.services.crawl_service import DailyCrawlService
from mongodb.api.services.classification_service import ClassificationService
from mongodb.api.services.pipeline_service import PipelineService

router = APIRouter()


class RawArticleInput(BaseModel):
    """Input schema cho bài báo thô từ Crawler"""
    url: str
    title: str
    content: Optional[str] = None
    text: Optional[str] = None  # Alternative to content
    source: str
    published_at: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []


class BatchIngestInput(BaseModel):
    """Input cho batch ingest"""
    articles: List[RawArticleInput]
    source_type: str = "rss"  # rss, google_news, manual


# Singleton pipeline instance
_pipeline: Optional[PipelineService] = None

def get_pipeline() -> PipelineService:
    global _pipeline
    if _pipeline is None:
        _pipeline = PipelineService()
    return _pipeline


@router.post("/crawl")
async def trigger_crawl(source: str, mode: str = "full"):
    """
    Trigger crawl thủ công cho một nguồn cụ thể
    
    Args:
        source: Tên nguồn (vnexpress, tuoitre, dantri, etc.)
        mode: Chế độ crawl (full, incremental)
    """
    try:
        service = DailyCrawlService()
        result = await service.crawl_source(source, mode)
        return {
            "success": True,
            "message": f"Crawl triggered for source: {source}",
            "mode": mode,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify")
async def classify_article(title: str, content: str):
    """
    Phân loại một bài báo sử dụng NLP
    
    Args:
        title: Tiêu đề bài báo
        content: Nội dung bài báo
        
    Returns:
        Kết quả phân loại bao gồm:
        - is_disaster: Có phải tin thiên tai không
        - disaster_type: Loại thiên tai
        - severity: Mức độ nghiêm trọng
        - confidence: Độ tin cậy
        - region: Vùng miền
        - matched_keywords: Từ khóa khớp
    """
    try:
        service = ClassificationService()
        result = await service.classify_article(title, content)
        return {
            "success": True,
            "classification": result.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_article(article: RawArticleInput):
    """
    Nhập một bài báo vào pipeline xử lý
    
    Luồng xử lý:
    1. Normalize dữ liệu
    2. Phân loại NLP
    3. Lưu MongoDB
    4. Broadcast WebSocket nếu là thiên tai
    """
    try:
        pipeline = get_pipeline()
        
        # Convert to dict for pipeline
        raw_data = article.model_dump()
        
        # Process through pipeline
        result = await pipeline.process_article(raw_data)
        
        if result:
            return {
                "success": True,
                "message": "Article processed successfully",
                "result": {
                    "url": result.original_url,
                    "is_disaster": result.is_disaster,
                    "disaster_type": result.disaster_type,
                    "severity": result.severity,
                    "confidence": result.confidence,
                    "region": result.region,
                    "matched_keywords": result.matched_keywords
                }
            }
        else:
            return {
                "success": False,
                "message": "Article could not be processed",
                "result": None
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/batch")
async def ingest_batch(batch: BatchIngestInput):
    """
    Nhập batch nhiều bài báo vào pipeline
    
    Args:
        batch: Danh sách bài báo và metadata
        
    Returns:
        Thống kê kết quả xử lý
    """
    try:
        pipeline = get_pipeline()
        
        # Convert to list of dicts
        raw_articles = [a.model_dump() for a in batch.articles]
        
        # Process batch
        results = await pipeline.process_batch(raw_articles)
        
        # Calculate stats
        disaster_count = sum(1 for r in results if r.is_disaster)
        
        return {
            "success": True,
            "message": f"Processed {len(results)}/{len(batch.articles)} articles",
            "stats": {
                "total_input": len(batch.articles),
                "processed": len(results),
                "failed": len(batch.articles) - len(results),
                "disaster_articles": disaster_count,
                "non_disaster": len(results) - disaster_count
            },
            "source_type": batch.source_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/stats")
async def get_pipeline_stats():
    """Lấy thống kê pipeline"""
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_stats()
        
        return {
            "success": True,
            "stats": stats.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/reset-stats")
async def reset_pipeline_stats():
    """Reset thống kê pipeline"""
    try:
        pipeline = get_pipeline()
        pipeline.reset_stats()
        
        return {
            "success": True,
            "message": "Pipeline stats reset",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/classify")
async def test_classification(
    articles: List[Dict[str, str]] = Body(
        ...,
        example=[
            {
                "title": "Bão số 3 đổ bộ Quảng Ninh gây thiệt hại nặng",
                "content": "Bão số 3 với sức gió mạnh cấp 12 đã đổ bộ vào Quảng Ninh sáng nay. Đã có 2 người chết và 10 người bị thương."
            }
        ]
    )
):
    """
    Test phân loại batch bài báo
    Sử dụng để debug và kiểm tra NLP classifier
    """
    try:
        service = ClassificationService()
        results = await service.classify_batch(articles)
        
        return {
            "success": True,
            "count": len(results),
            "results": [r.model_dump() for r in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/json")
async def import_from_json(
    file_path: str = Body(..., embed=True, description="Path to JSON file"),
    classify: bool = Body(True, embed=True, description="Run NLP classification")
):
    """
    Import articles from a JSON file into MongoDB
    
    Args:
        file_path: Path to JSON file (relative or absolute)
        classify: Whether to run NLP classification
    """
    import json
    import os
    from mongodb.api.config.database import get_database
    
    try:
        # Handle relative paths
        if not os.path.isabs(file_path):
            # Try public folder first
            possible_paths = [
                file_path,
                os.path.join("public", file_path),
                os.path.join(os.getcwd(), file_path),
                os.path.join(os.getcwd(), "public", file_path),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Load JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not isinstance(articles, list):
            articles = [articles]
        
        db = get_database()
        collection = db.articles
        
        # Process each article
        processed = 0
        skipped = 0
        classifier = ClassificationService() if classify else None
        
        for article in articles:
            try:
                # Skip if already exists
                if collection.find_one({"url": article.get("url")}):
                    skipped += 1
                    continue
                
                # Run classification if enabled
                if classifier:
                    title = article.get("title", "")
                    content = article.get("text") or article.get("summary") or ""
                    
                    if title or content:
                        result = await classifier.classify_article(title, content)
                        article["is_disaster"] = result.is_disaster
                        article["disaster_type"] = result.disaster_type
                        article["severity"] = result.severity
                        article["confidence"] = result.confidence
                        article["region"] = result.region
                        article["matched_keywords"] = result.matched_keywords
                    else:
                        article["is_disaster"] = False
                
                # Insert into MongoDB
                collection.insert_one(article)
                processed += 1
                
            except Exception as e:
                print(f"Error processing article: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Imported {processed} articles from {file_path}",
            "stats": {
                "total_in_file": len(articles),
                "processed": processed,
                "skipped_duplicates": skipped,
                "failed": len(articles) - processed - skipped
            },
            "classification_enabled": classify,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/stats")
async def get_database_stats():
    """Get MongoDB collection statistics"""
    from mongodb.api.config.database import get_database
    
    try:
        db = get_database()
        
        total = db.articles.count_documents({})
        disaster = db.articles.count_documents({"is_disaster": True})
        by_severity = {
            "high": db.articles.count_documents({"severity": "high"}),
            "medium": db.articles.count_documents({"severity": "medium"}),
            "low": db.articles.count_documents({"severity": "low"})
        }
        
        # Get source distribution
        sources_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        sources = list(db.articles.aggregate(sources_pipeline))
        
        return {
            "success": True,
            "stats": {
                "total_articles": total,
                "disaster_articles": disaster,
                "non_disaster": total - disaster,
                "by_severity": by_severity,
                "by_source": {s["_id"]: s["count"] for s in sources}
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))