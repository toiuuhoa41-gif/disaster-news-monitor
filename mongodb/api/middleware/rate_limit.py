"""
Rate Limiting Middleware using SlowAPI
Protects API endpoints from abuse
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request
    Handles proxy headers (X-Forwarded-For, X-Real-IP)
    """
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    if request.client:
        return request.client.host
    
    return "127.0.0.1"


# Create limiter instance
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["200 per minute", "5000 per hour"],
    storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
    strategy="fixed-window",
    headers_enabled=True,
)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    # Public endpoints - more restrictive
    "public": "60/minute",
    
    # Read operations - moderate
    "read": "100/minute",
    
    # Write operations - more restrictive
    "write": "30/minute",
    
    # Crawl operations - very restrictive (resource intensive)
    "crawl": "5/minute",
    
    # Authentication - prevent brute force
    "auth": "10/minute",
    
    # WebSocket - allow more connections
    "websocket": "20/minute",
    
    # Dashboard stats - cached, allow more
    "dashboard": "120/minute",
}


def rate_limit(limit_type: str = "read"):
    """
    Decorator factory for rate limiting
    
    Usage:
        @router.get("/items")
        @rate_limit("read")
        async def get_items():
            ...
    """
    limit_string = RATE_LIMITS.get(limit_type, RATE_LIMITS["read"])
    return limiter.limit(limit_string)


def setup_rate_limiting(app):
    """
    Setup rate limiting for FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Add limiter state to app
    app.state.limiter = limiter
    
    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Add custom middleware that skips OPTIONS requests
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Skip rate limiting for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip health check endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        return await call_next(request)
    
    logger.info("🛡️ Rate limiting enabled")


# Custom rate limit exceeded handler with JSON response
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded"""
    from fastapi.responses import JSONResponse
    
    retry_after = exc.detail.split("per")[0].strip() if exc.detail else "60"
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Please try again later.",
            "detail": str(exc.detail),
            "retry_after": retry_after
        },
        headers={
            "Retry-After": retry_after,
            "X-RateLimit-Limit": str(exc.detail),
        }
    )
