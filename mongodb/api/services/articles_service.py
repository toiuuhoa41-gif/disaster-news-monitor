"""
Articles Service - Async MongoDB Operations
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from mongodb.api.schemas.article import ArticleCreate, ArticleUpdate, ArticleFilter
from mongodb.api.config.database import Database, get_articles_collection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class ArticlesService:
    """Service for article CRUD operations using async MongoDB"""
    
    def __init__(self):
        self._collection = None
    
    @property
    def collection(self):
        """Get articles collection (lazy initialization)"""
        if self._collection is None:
            self._collection = get_articles_collection()
        return self._collection

    def _build_query(self, filters: Optional[ArticleFilter] = None, search: Optional[str] = None) -> Dict[str, Any]:
        """Build MongoDB query from filters"""
        query = {}
        
        if filters:
            if filters.from_date:
                query.setdefault("$and", []).append({
                    "$or": [
                        {"publish_date": {"$gte": filters.from_date}},
                        {"collected_at": {"$gte": filters.from_date}}
                    ]
                })
            if filters.to_date:
                query.setdefault("$and", []).append({
                    "$or": [
                        {"publish_date": {"$lte": filters.to_date}},
                        {"collected_at": {"$lte": filters.to_date}}
                    ]
                })
            if filters.region:
                query['region'] = {"$regex": filters.region, "$options": "i"}
            if filters.disaster_type:
                query['disaster_type'] = {"$regex": filters.disaster_type, "$options": "i"}
            if filters.severity:
                query['severity'] = filters.severity
            if filters.source:
                query['source'] = {"$regex": filters.source, "$options": "i"}
        
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"summary": {"$regex": search, "$options": "i"}},
                {"text": {"$regex": search, "$options": "i"}},
                {"keywords": {"$regex": search, "$options": "i"}}
            ]
        
        return query

    def _serialize_article(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert MongoDB document to serializable dict"""
        if doc is None:
            return None
        
        # Convert ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        return doc

    async def get_latest_articles(
        self, 
        limit: int = 20, 
        severity: Optional[str] = None, 
        type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get latest articles with optional filters"""
        query = {}
        if severity:
            query['severity'] = severity
        if type:
            query['disaster_type'] = type
        
        try:
            cursor = self.collection.find(query).sort("collected_at", -1).limit(limit)
            articles = await cursor.to_list(length=limit)
        except Exception as e:
            logger.warning(f"Error with sort field, using default: {e}")
            cursor = self.collection.find(query).limit(limit)
            articles = await cursor.to_list(length=limit)
        
        return [self._serialize_article(a) for a in articles]

    async def get_articles(
        self, 
        filters: Optional[ArticleFilter] = None, 
        limit: int = 20, 
        skip: int = 0,
        sort_by: str = "collected_at",
        sort_order: str = "desc",
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get articles with filters, pagination and sorting"""
        query = self._build_query(filters, search)
        
        # Determine sort direction
        sort_direction = -1 if sort_order == "desc" else 1
        
        # Valid sort fields
        valid_sort_fields = ["collected_at", "publish_date", "title", "source", "severity", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "collected_at"
        
        try:
            cursor = self.collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)
            articles = await cursor.to_list(length=limit)
        except Exception as e:
            logger.warning(f"Error with query/sort: {e}")
            cursor = self.collection.find(query).skip(skip).limit(limit)
            articles = await cursor.to_list(length=limit)
        
        return [self._serialize_article(a) for a in articles]

    async def get_total_count(
        self, 
        filters: Optional[ArticleFilter] = None, 
        search: Optional[str] = None
    ) -> int:
        """Get total count of articles matching filters"""
        query = self._build_query(filters, search)
        return await self.collection.count_documents(query)

    async def get_articles_with_filter(
        self, 
        from_date: str, 
        to_date: str, 
        region: Optional[str] = None, 
        disaster_type: Optional[str] = None, 
        severity: Optional[str] = None, 
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get articles within date range with optional filters"""
        query = {
            "published_at": {
                "$gte": from_date,
                "$lte": to_date
            }
        }
        if region:
            query['region'] = region
        if disaster_type:
            query['disaster_type'] = disaster_type
        if severity:
            query['severity'] = severity
        if source:
            query['source'] = source
        
        cursor = self.collection.find(query)
        articles = await cursor.to_list(length=1000)
        return [self._serialize_article(a) for a in articles]

    async def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a single article by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(article_id)})
        except Exception:
            doc = await self.collection.find_one({"_id": article_id})
        
        return self._serialize_article(doc)

    async def create_article(self, article: ArticleCreate) -> Dict[str, Any]:
        """Create a new article"""
        article_data = article.model_dump()
        result = await self.collection.insert_one(article_data)
        article_data['_id'] = str(result.inserted_id)
        
        # Publish to WebSocket if disaster article
        if article_data.get('is_disaster'):
            try:
                from mongodb.api.websockets.disaster_feed import broadcast_disaster_article
                await broadcast_disaster_article(article_data)
            except Exception as e:
                logger.warning(f"Failed to broadcast article: {e}")
        
        return article_data

    async def create_many_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Create multiple articles at once"""
        if not articles:
            return []
        
        result = await self.collection.insert_many(articles)
        return [str(id) for id in result.inserted_ids]

    async def update_article(self, article_id: str, article: ArticleUpdate) -> Dict[str, Any]:
        """Update an existing article"""
        update_data = article.model_dump(exclude_unset=True)
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(article_id)}, 
                {"$set": update_data}
            )
        except Exception:
            result = await self.collection.update_one(
                {"_id": article_id}, 
                {"$set": update_data}
            )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return await self.get_article_by_id(article_id)

    async def delete_article(self, article_id: str) -> None:
        """Delete an article by ID"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(article_id)})
        except Exception:
            result = await self.collection.delete_one({"_id": article_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Article not found")

    async def check_url_exists(self, url: str) -> bool:
        """Check if article with URL already exists"""
        doc = await self.collection.find_one({"url": url})
        return doc is not None

    async def get_stats(self) -> Dict[str, Any]:
        """Get article statistics"""
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_severity": [
                        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
                    ],
                    "by_region": [
                        {"$group": {"_id": "$region", "count": {"$sum": 1}}}
                    ],
                    "by_disaster_type": [
                        {"$group": {"_id": "$disaster_type", "count": {"$sum": 1}}}
                    ],
                    "by_source": [
                        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ]
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {"total": 0, "by_severity": {}, "by_region": {}, "by_disaster_type": {}, "by_source": {}}
        
        stats = result[0]
        return {
            "total": stats["total"][0]["count"] if stats["total"] else 0,
            "by_severity": {item["_id"]: item["count"] for item in stats["by_severity"] if item["_id"]},
            "by_region": {item["_id"]: item["count"] for item in stats["by_region"] if item["_id"]},
            "by_disaster_type": {item["_id"]: item["count"] for item in stats["by_disaster_type"] if item["_id"]},
            "by_source": {item["_id"]: item["count"] for item in stats["by_source"] if item["_id"]}
        }