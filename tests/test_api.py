"""
Test API Endpoints
"""

import pytest
from httpx import AsyncClient


class TestSystemEndpoints:
    """Test system and health check endpoints"""
    
    @pytest.mark.asyncio
    async def test_root(self, app_client: AsyncClient):
        """Test root endpoint"""
        response = await app_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_health_check(self, app_client: AsyncClient):
        """Test health check endpoint"""
        response = await app_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_user(self, app_client: AsyncClient):
        """Test user registration"""
        user_data = {
            "username": "newuser",
            "password": "securepassword123",
            "email": "newuser@example.com"
        }
        
        response = await app_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, app_client: AsyncClient):
        """Test duplicate user registration fails"""
        user_data = {
            "username": "duplicateuser",
            "password": "password123"
        }
        
        # First registration
        await app_client.post("/api/v1/auth/register", json=user_data)
        
        # Second registration should fail
        response = await app_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_login(self, app_client: AsyncClient):
        """Test user login"""
        # Register user first
        user_data = {
            "username": "loginuser",
            "password": "password123"
        }
        await app_client.post("/api/v1/auth/register", json=user_data)
        
        # Login
        response = await app_client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, app_client: AsyncClient):
        """Test login with wrong password"""
        # Register user first
        await app_client.post("/api/v1/auth/register", json={
            "username": "wrongpassuser",
            "password": "correctpassword"
        })
        
        # Login with wrong password
        response = await app_client.post(
            "/api/v1/auth/login",
            json={"username": "wrongpassuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, app_client: AsyncClient, auth_headers: dict):
        """Test get current user endpoint"""
        response = await app_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestArticleEndpoints:
    """Test article endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_articles(self, app_client: AsyncClient):
        """Test get articles list"""
        response = await app_client.get("/api/v1/articles/")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_latest_articles(self, app_client: AsyncClient):
        """Test get latest articles"""
        response = await app_client.get("/api/v1/articles/latest")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_articles_with_filters(self, app_client: AsyncClient):
        """Test get articles with query parameters"""
        response = await app_client.get(
            "/api/v1/articles/",
            params={
                "limit": 10,
                "severity": "high",
                "sort_by": "collected_at",
                "sort_order": "desc"
            }
        )
        assert response.status_code == 200


class TestDashboardEndpoints:
    """Test dashboard endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_overview(self, app_client: AsyncClient):
        """Test dashboard overview"""
        response = await app_client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200


class TestRealtimeEndpoints:
    """Test realtime endpoints"""
    
    @pytest.mark.asyncio
    async def test_realtime_status(self, app_client: AsyncClient):
        """Test realtime status endpoint"""
        response = await app_client.get("/api/v1/realtime/status")
        assert response.status_code == 200
