"""
Pipeline Service - Điều phối luồng dữ liệu từ Crawler -> MongoDB -> WebSocket

Kiến trúc:
1. Crawler (RSS/Google News) -> Raw Articles
2. Normalizer -> Normalized Articles  
3. NLP Classifier -> Classified Articles
4. MongoDB -> Storage
5. WebSocket -> Real-time Dashboard
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio

from mongodb.api.config.database import Database
from mongodb.api.services.normalizer_service import NormalizerService, NormalizedArticle
from mongodb.api.services.classification_service import ClassificationService, ClassificationResult
from mongodb.api.services.websocket_service import WebSocketService
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProcessedArticle(BaseModel):
    """Bài báo đã qua toàn bộ pipeline"""
    # Original data
    original_url: str
    source: str
    
    # Normalized data
    title: str
    content: str
    published_at: Optional[datetime] = None
    
    # Classification result
    is_disaster: bool
    disaster_type: str
    severity: str
    confidence: float
    region: Optional[str] = None
    matched_keywords: List[str] = []
    
    # Metadata
    processed_at: datetime
    pipeline_version: str = "1.0"
    
    class Config:
        from_attributes = True


class PipelineStats(BaseModel):
    """Thống kê pipeline"""
    total_processed: int = 0
    disaster_articles: int = 0
    non_disaster_articles: int = 0
    failed_articles: int = 0
    avg_confidence: float = 0.0
    processing_time_ms: float = 0.0


class PipelineService:
    """
    Main Pipeline Service
    
    Orchestrates the flow:
    Raw Article -> Normalize -> Classify -> Store -> Broadcast
    """
    
    def __init__(self):
        self.normalizer = NormalizerService()
        self.classifier = ClassificationService()
        self.websocket = WebSocketService()
        
        # Pipeline stats
        self.stats = PipelineStats()
    
    @property
    def db(self):
        return Database.get_db()
    
    async def process_article(self, raw_article: Dict[str, Any]) -> Optional[ProcessedArticle]:
        """
        Xử lý một bài báo qua toàn bộ pipeline
        
        Args:
            raw_article: Dữ liệu bài báo thô từ Crawler
            
        Returns:
            ProcessedArticle nếu thành công, None nếu thất bại
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Normalize
            normalized = await self.normalizer.normalize_article(raw_article)
            if not normalized:
                logger.warning(f"Failed to normalize article: {raw_article.get('url', 'unknown')}")
                self.stats.failed_articles += 1
                return None
            
            # Step 2: Classify
            classification = await self.classifier.classify_article(
                normalized.title,
                normalized.content
            )
            
            # Step 3: Create processed article
            processed = ProcessedArticle(
                original_url=normalized.url,
                source=normalized.source,
                title=normalized.title,
                content=normalized.content,
                published_at=normalized.published_at,
                is_disaster=classification.is_disaster,
                disaster_type=classification.disaster_type,
                severity=classification.severity,
                confidence=classification.confidence,
                region=classification.region,
                matched_keywords=classification.matched_keywords,
                processed_at=datetime.now()
            )
            
            # Step 4: Store in MongoDB
            await self._store_article(processed)
            
            # Step 5: Broadcast if disaster
            if processed.is_disaster:
                await self._broadcast_disaster(processed)
                self.stats.disaster_articles += 1
            else:
                self.stats.non_disaster_articles += 1
            
            # Update stats
            self.stats.total_processed += 1
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_avg_confidence(classification.confidence)
            
            logger.info(
                f"Processed article: {processed.title[:50]}... | "
                f"disaster={processed.is_disaster} | "
                f"confidence={processed.confidence:.2f} | "
                f"time={processing_time:.0f}ms"
            )
            
            return processed
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self.stats.failed_articles += 1
            return None
    
    async def process_batch(self, raw_articles: List[Dict[str, Any]]) -> List[ProcessedArticle]:
        """
        Xử lý batch nhiều bài báo
        
        Args:
            raw_articles: Danh sách bài báo thô
            
        Returns:
            Danh sách bài báo đã xử lý thành công
        """
        results = []
        
        for raw in raw_articles:
            processed = await self.process_article(raw)
            if processed:
                results.append(processed)
        
        logger.info(f"Batch processed: {len(results)}/{len(raw_articles)} successful")
        return results
    
    async def _store_article(self, article: ProcessedArticle):
        """Lưu bài báo vào MongoDB"""
        try:
            collection = self.db["articles"]
            
            # Check for duplicates
            existing = await collection.find_one({"url": article.original_url})
            
            if existing:
                # Update existing
                await collection.update_one(
                    {"url": article.original_url},
                    {"$set": article.model_dump()}
                )
            else:
                # Insert new
                doc = article.model_dump()
                doc["url"] = article.original_url
                doc["created_at"] = datetime.now()
                await collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing article: {e}")
    
    async def _broadcast_disaster(self, article: ProcessedArticle):
        """Broadcast bài báo thiên tai qua WebSocket"""
        try:
            message = {
                "type": "new_disaster",
                "data": {
                    "title": article.title,
                    "source": article.source,
                    "url": article.original_url,
                    "disaster_type": article.disaster_type,
                    "severity": article.severity,
                    "region": article.region,
                    "confidence": article.confidence,
                    "matched_keywords": article.matched_keywords,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "processed_at": article.processed_at.isoformat()
                }
            }
            await self.websocket.broadcast(message)
        except Exception as e:
            logger.error(f"Error broadcasting: {e}")
    
    def _update_avg_confidence(self, new_confidence: float):
        """Cập nhật confidence trung bình"""
        total = self.stats.total_processed
        if total == 0:
            self.stats.avg_confidence = new_confidence
        else:
            current = self.stats.avg_confidence
            self.stats.avg_confidence = (current * total + new_confidence) / (total + 1)
    
    def get_stats(self) -> PipelineStats:
        """Lấy thống kê pipeline"""
        return self.stats
    
    def reset_stats(self):
        """Reset thống kê"""
        self.stats = PipelineStats()


class RealtimePipelineService:
    """
    Service chạy pipeline liên tục
    Kết nối với RSS Crawler để xử lý bài mới
    """
    
    def __init__(self):
        self.pipeline = PipelineService()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, interval_seconds: int = 300):
        """Bắt đầu pipeline realtime"""
        self.is_running = True
        logger.info(f"Starting realtime pipeline with {interval_seconds}s interval")
        
        while self.is_running:
            try:
                # Fetch new articles from crawler
                new_articles = await self._fetch_new_articles()
                
                if new_articles:
                    # Process through pipeline
                    await self.pipeline.process_batch(new_articles)
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Realtime pipeline error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def stop(self):
        """Dừng pipeline"""
        self.is_running = False
        logger.info("Stopping realtime pipeline")
    
    async def _fetch_new_articles(self) -> List[Dict[str, Any]]:
        """
        Lấy bài mới từ crawler
        Có thể kết nối với:
        - crawl/realtime_rss_monitor.py
        - External API
        - Message queue (Redis, RabbitMQ)
        """
        try:
            db = Database.get_db()
            collection = db["raw_articles"]
            
            # Get unprocessed articles
            cursor = collection.find(
                {"processed": {"$ne": True}}
            ).limit(50)
            
            articles = await cursor.to_list(length=50)
            
            # Mark as processing
            if articles:
                ids = [a["_id"] for a in articles]
                await collection.update_many(
                    {"_id": {"$in": ids}},
                    {"$set": {"processing": True}}
                )
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching new articles: {e}")
            return []
