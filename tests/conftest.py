"""
Pytest Configuration and Fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "disaster_monitor_test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def mongo_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create MongoDB client for tests"""
    client = AsyncIOMotorClient(os.environ["MONGO_URI"])
    yield client
    client.close()


@pytest.fixture(scope="function")
async def test_db(mongo_client: AsyncIOMotorClient):
    """Create test database and clean up after each test"""
    db = mongo_client[os.environ["DATABASE_NAME"]]
    
    yield db
    
    # Cleanup - drop all collections after each test
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].drop()


@pytest.fixture(scope="function")
async def app_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for API testing"""
    from mongodb.api.main import app
    from mongodb.api.config.database import Database
    
    # Connect to test database
    await Database.connect(
        os.environ["MONGO_URI"],
        os.environ["DATABASE_NAME"]
    )
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    # Disconnect after tests
    await Database.disconnect()


@pytest.fixture
async def auth_headers(app_client: AsyncClient) -> dict:
    """Get authentication headers with valid JWT token"""
    # Create test user
    user_data = {
        "username": "testuser",
        "password": "testpassword123",
        "email": "test@example.com",
        "role": "admin"
    }
    
    await app_client.post("/api/v1/auth/register", json=user_data)
    
    # Login to get token
    login_response = await app_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword123"}
    )
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_article() -> dict:
    """Sample article for testing"""
    return {
        "title": "Bão số 9 đổ bộ vào miền Trung",
        "summary": "Bão số 9 với sức gió mạnh cấp 12-13 đổ bộ vào Quảng Nam - Quảng Ngãi",
        "source": "vnexpress.net",
        "url": "https://vnexpress.net/bao-so-9-do-bo-12345.html",
        "text": "Theo Trung tâm Dự báo khí tượng thủy văn quốc gia, bão số 9 đã đổ bộ vào đất liền...",
        "disaster_type": "weather",
        "severity": "high",
        "region": "central",
        "keywords": ["bão", "miền trung", "thiên tai"],
        "publish_date": "2024-01-15T10:00:00Z",
        "collected_at": "2024-01-15T10:30:00Z"
    }


@pytest.fixture
def sample_source() -> dict:
    """Sample news source for testing"""
    return {
        "name": "VnExpress",
        "domain": "vnexpress.net",
        "url": "https://vnexpress.net/rss/thoi-su.rss",
        "type": "rss",
        "is_active": True,
        "categories": ["Thời sự", "Thiên tai"]
    }
