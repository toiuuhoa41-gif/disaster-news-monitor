"""
Async MongoDB Database Configuration using Motor
Provides connection pooling and async operations
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

# Environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "disaster_monitor")


class Database:
    """Async MongoDB Database Manager with Connection Pooling"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls, uri: str = MONGO_URI, db_name: str = DATABASE_NAME):
        """Connect to MongoDB with connection pooling"""
        try:
            cls.client = AsyncIOMotorClient(
                uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True,
                retryReads=True
            )
            
            # Verify connection
            await cls.client.admin.command('ping')
            cls.db = cls.client[db_name]
            
            logger.info(f"✅ Connected to MongoDB: {db_name}")
            
            # Create indexes
            await cls._create_indexes()
            
            return cls.db
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("🔌 Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for optimized queries"""
        if cls.db is None:
            return
        
        try:
            # Articles collection indexes
            articles = cls.db.articles
            await articles.create_index([("collected_at", DESCENDING)])
            await articles.create_index([("publish_date", DESCENDING)])
            await articles.create_index([("source", ASCENDING)])
            await articles.create_index([("disaster_type", ASCENDING)])
            await articles.create_index([("severity", ASCENDING)])
            await articles.create_index([("region", ASCENDING)])
            await articles.create_index([("url", ASCENDING)], unique=True, sparse=True)
            
            # Text index with "none" language for Vietnamese support
            # First, try to drop any existing text index with wrong language
            try:
                # Check if text index exists and drop it first
                existing_indexes = await articles.index_information()
                for idx_name, idx_info in existing_indexes.items():
                    if any(field == "text" for _, field in idx_info.get("key", [])):
                        await articles.drop_index(idx_name)
                        logger.info(f"Dropped old text index: {idx_name}")
                        break
                
                await articles.create_index(
                    [("title", "text"), ("summary", "text"), ("text", "text")],
                    default_language="none",  # Disable language-specific stemming for Vietnamese
                    name="text_search_index"
                )
            except Exception as text_idx_error:
                # If it still fails, text search won't be available but app will work
                logger.warning(f"Could not create text index: {text_idx_error}")
            
            # Sources collection indexes
            sources = cls.db.sources
            await sources.create_index([("domain", ASCENDING)], unique=True, sparse=True)
            await sources.create_index([("is_active", ASCENDING)])
            
            # Keywords collection indexes
            keywords = cls.db.keywords
            await keywords.create_index([("keyword", ASCENDING)])
            await keywords.create_index([("count", DESCENDING)])
            
            # Users collection indexes (for auth)
            users = cls.db.users
            await users.create_index([("username", ASCENDING)], unique=True)
            await users.create_index([("email", ASCENDING)], unique=True, sparse=True)
            
            logger.info("📑 Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating indexes: {e}")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.db
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name"""
        return cls.get_db()[name]


# Dependency injection helper
async def get_database() -> AsyncIOMotorDatabase:
    """Return the async database instance (FastAPI dependency)"""
    return Database.get_db()


def get_articles_collection():
    """Get articles collection"""
    return Database.get_collection("articles")


def get_sources_collection():
    """Get sources collection"""
    return Database.get_collection("sources")


def get_keywords_collection():
    """Get keywords collection"""
    return Database.get_collection("keywords")


def get_users_collection():
    """Get users collection for authentication"""
    return Database.get_collection("users")