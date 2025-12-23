from typing import List, Dict
from bson import ObjectId
import logging
from mongodb.api.config.database import Database

# Setup logging
logger = logging.getLogger(__name__)


class KeywordsService:
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def collection(self):
        return self.db['keywords']

    async def get_all_keywords(self) -> List[Dict]:
        """Retrieve all keywords."""
        try:
            cursor = self.collection.find({})
            keywords = await cursor.to_list(length=None)
            return keywords
        except Exception as e:
            logger.error(f"Error retrieving keywords: {e}")
            return []

    async def get_keywords(self) -> Dict[str, List[str]]:
        """Retrieve all keyword groups for disaster types."""
        try:
            cursor = self.collection.find({})
            keywords = await cursor.to_list(length=None)
            keyword_groups = {}
            for keyword in keywords:
                keyword_groups[keyword.get('type', 'general')] = keyword.get('words', [])
            return keyword_groups
        except Exception as e:
            logger.error(f"Error retrieving keywords: {e}")
            return {}

    async def add_keyword(self, keyword) -> Dict:
        """Add a new keyword."""
        try:
            data = keyword.model_dump() if hasattr(keyword, 'model_dump') else keyword
            result = await self.collection.insert_one(data)
            return await self.collection.find_one({"_id": result.inserted_id})
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            raise

    async def delete_keyword(self, keyword_id: str) -> bool:
        """Delete a keyword by ID."""
        try:
            result = await self.collection.delete_one({'_id': ObjectId(keyword_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting keyword: {e}")
            return False

    async def get_keyword_by_id(self, keyword_id: str) -> Dict:
        """Retrieve a keyword by its ID."""
        try:
            keyword = await self.collection.find_one({'_id': ObjectId(keyword_id)})
            return keyword
        except Exception as e:
            logger.error(f"Error retrieving keyword by ID: {e}")
            return {}


class KeywordsUpdateService:
    """Service for updating keywords"""
    
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def collection(self):
        return self.db['keywords']

    async def update_keywords(self) -> Dict:
        """Update keywords from configured sources"""
        try:
            # Placeholder for actual keyword update logic
            keywords_count = await self.collection.count_documents({})
            return {
                "status": "updated",
                "keywords_count": keywords_count,
                "updated_at": str(ObjectId())
            }
        except Exception as e:
            logger.error(f"Error updating keywords: {e}")
            return {"error": str(e)}