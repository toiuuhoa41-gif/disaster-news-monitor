"""
Application Settings with Environment Variable Support
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Application settings
    app_name: str = "Disaster Monitor"
    app_version: str = "2.0.0"
    api_version: str = "v1"
    debug: bool = True  # Enable debug for development
    environment: str = "development"  # development, staging, production

    # Database settings
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "disaster_monitor"
    database_url: Optional[str] = None

    # Redis settings (for pub/sub and caching)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Security settings
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS settings - comma separated origins
    cors_origins: str = "*"  # Allow all origins in development
    cors_allow_credentials: bool = False  # Must be False with wildcard origin
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # WebSocket settings
    websocket_url: str = "ws://localhost:8000/realtime/ws/disasters"
    ws_heartbeat_interval: int = 30

    # Scheduler settings
    scheduler_timezone: str = "Asia/Ho_Chi_Minh"
    crawl_interval_minutes: int = 15

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Crawler settings
    crawler_user_agent: str = "DisasterMonitor/2.0 (+https://github.com/disaster-monitor)"
    crawler_timeout: int = 30
    crawler_max_retries: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()