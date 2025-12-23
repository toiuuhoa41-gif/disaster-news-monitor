"""
Test Database Operations
"""

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime


class TestDatabaseOperations:
    """Test MongoDB operations"""
    
    @pytest.mark.asyncio
    async def test_insert_article(self, test_db: AsyncIOMotorDatabase, sample_article: dict):
        """Test inserting an article"""
        articles = test_db.articles
        result = await articles.insert_one(sample_article)
        
        assert result.inserted_id is not None
        assert isinstance(result.inserted_id, ObjectId)
    
    @pytest.mark.asyncio
    async def test_find_article_by_id(self, test_db: AsyncIOMotorDatabase, sample_article: dict):
        """Test finding article by ID"""
        articles = test_db.articles
        insert_result = await articles.insert_one(sample_article)
        
        found = await articles.find_one({"_id": insert_result.inserted_id})
        
        assert found is not None
        assert found["title"] == sample_article["title"]
    
    @pytest.mark.asyncio
    async def test_find_articles_by_severity(self, test_db: AsyncIOMotorDatabase):
        """Test filtering articles by severity"""
        articles = test_db.articles
        
        # Insert articles with different severities
        await articles.insert_many([
            {"title": "High severity", "severity": "high"},
            {"title": "Medium severity", "severity": "medium"},
            {"title": "Low severity", "severity": "low"},
        ])
        
        high_articles = await articles.find({"severity": "high"}).to_list(length=100)
        
        assert len(high_articles) == 1
        assert high_articles[0]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_update_article(self, test_db: AsyncIOMotorDatabase, sample_article: dict):
        """Test updating an article"""
        articles = test_db.articles
        insert_result = await articles.insert_one(sample_article)
        
        await articles.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"severity": "medium"}}
        )
        
        updated = await articles.find_one({"_id": insert_result.inserted_id})
        assert updated["severity"] == "medium"
    
    @pytest.mark.asyncio
    async def test_delete_article(self, test_db: AsyncIOMotorDatabase, sample_article: dict):
        """Test deleting an article"""
        articles = test_db.articles
        insert_result = await articles.insert_one(sample_article)
        
        await articles.delete_one({"_id": insert_result.inserted_id})
        
        deleted = await articles.find_one({"_id": insert_result.inserted_id})
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_count_articles(self, test_db: AsyncIOMotorDatabase):
        """Test counting articles"""
        articles = test_db.articles
        
        await articles.insert_many([
            {"title": "Article 1"},
            {"title": "Article 2"},
            {"title": "Article 3"},
        ])
        
        count = await articles.count_documents({})
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_text_search(self, test_db: AsyncIOMotorDatabase):
        """Test text search on articles"""
        articles = test_db.articles
        
        # Create text index
        await articles.create_index([("title", "text"), ("summary", "text")])
        
        # Insert articles
        await articles.insert_many([
            {"title": "Bão số 9 đổ bộ", "summary": "Bão gây thiệt hại lớn"},
            {"title": "Động đất ở Kon Tum", "summary": "Rung chấn mạnh"},
            {"title": "Tin tức thể thao", "summary": "Bóng đá Việt Nam"},
        ])
        
        # Search for "bão"
        results = await articles.find({"$text": {"$search": "bão"}}).to_list(length=100)
        
        assert len(results) == 1
        assert "Bão" in results[0]["title"]
    
    @pytest.mark.asyncio
    async def test_aggregation_by_region(self, test_db: AsyncIOMotorDatabase):
        """Test aggregation by region"""
        articles = test_db.articles
        
        await articles.insert_many([
            {"title": "Article 1", "region": "north"},
            {"title": "Article 2", "region": "central"},
            {"title": "Article 3", "region": "central"},
            {"title": "Article 4", "region": "south"},
        ])
        
        pipeline = [
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await articles.aggregate(pipeline).to_list(length=100)
        
        assert len(results) == 3
        # Central should have highest count
        assert results[0]["_id"] == "central"
        assert results[0]["count"] == 2
