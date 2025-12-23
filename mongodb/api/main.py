"""
Disaster Monitor API - Main Application
FastAPI application with async MongoDB, JWT auth, Redis pub/sub, and integrated scheduler
"""

from fastapi import FastAPI, Request, status, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import time
import logging
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from mongodb.api.config.settings import settings
from mongodb.api.config.database import Database
from mongodb.api.utils.logger import setup_logging, get_logger
from mongodb.api.routers import (
    system, articles, dashboard, sources, 
    keywords, regions, realtime, internal, auth
)
from mongodb.api.routers import crawl as crawl_router
from mongodb.api.websockets.disaster_feed import manager as ws_manager
from mongodb.api.middleware.rate_limit import limiter, setup_rate_limiting

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# ============================================
# Scheduler Configuration
# ============================================

scheduler = AsyncIOScheduler(timezone='Asia/Ho_Chi_Minh')

# Import services for scheduled tasks
from mongodb.api.services.stats_service import StatsUpdateService
from mongodb.api.services.maintenance_service import MaintenanceService
from mongodb.api.services.sources_service import SourcesHealthService
from mongodb.api.services.keywords_service import KeywordsUpdateService
from mongodb.api.services.crawl_service import DailyCrawlService


async def scheduled_crawl():
    """Daily crawl from all sources - runs at 00:05"""
    try:
        logger.info("🌐 [Scheduler] Running daily crawl...")
        service = DailyCrawlService()
        result = await service.crawl_all_sources()
        stored = result.get('total', {}).get('stored', 0)
        logger.info(f"✅ [Scheduler] Crawl completed: {stored} new articles")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Crawl failed: {e}")


async def scheduled_health_check():
    """Daily sources health check - runs at 00:00"""
    try:
        logger.info("🏥 [Scheduler] Running daily health check...")
        service = SourcesHealthService()
        result = await service.check_all_sources()
        logger.info(f"✅ [Scheduler] Health check completed: {result}")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Health check failed: {e}")


async def scheduled_stats_update():
    """Update statistics - runs at 00:30"""
    try:
        logger.info("📊 [Scheduler] Running stats update...")
        service = StatsUpdateService()
        result = await service.update_daily_stats()
        logger.info(f"✅ [Scheduler] Stats update completed: {result}")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Stats update failed: {e}")


async def scheduled_keywords_update():
    """Update keywords - runs at 01:00"""
    try:
        logger.info("🔍 [Scheduler] Running keywords update...")
        service = KeywordsUpdateService()
        result = await service.update_keywords()
        logger.info(f"✅ [Scheduler] Keywords update completed: {result}")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Keywords update failed: {e}")


async def scheduled_maintenance():
    """Daily maintenance cleanup - runs at 01:30"""
    try:
        logger.info("🧹 [Scheduler] Running daily maintenance...")
        service = MaintenanceService()
        result = await service.daily_cleanup()
        logger.info(f"✅ [Scheduler] Maintenance completed: {result}")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Maintenance failed: {e}")


# ============================================
# Application Lifespan
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"📍 Environment: {settings.environment}")
    
    # Connect to MongoDB
    try:
        await Database.connect(settings.mongo_uri, settings.mongo_db)
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    # Connect to Redis (optional)
    try:
        from mongodb.api.services.redis_service import RedisService
        await RedisService.connect()
        await ws_manager.setup_redis_subscriber()
    except Exception as e:
        logger.warning(f"Redis not available: {e}. WebSocket will use local broadcast.")
    
    # Start Scheduler
    try:
        # Daily crawl at 00:05 (first job of the day)
        scheduler.add_job(
            scheduled_crawl,
            trigger=CronTrigger(hour=0, minute=5),
            id="daily_crawl",
            name="Daily News Crawl",
            replace_existing=True
        )
        
        # Daily health check at 00:00
        scheduler.add_job(
            scheduled_health_check,
            trigger=CronTrigger(hour=0, minute=0),
            id="daily_health_check",
            name="Daily Sources Health Check",
            replace_existing=True
        )
        
        # Stats update at 00:30
        scheduler.add_job(
            scheduled_stats_update,
            trigger=CronTrigger(hour=0, minute=30),
            id="daily_stats_update",
            name="Daily Statistics Update",
            replace_existing=True
        )
        
        # Keywords update at 01:00
        scheduler.add_job(
            scheduled_keywords_update,
            trigger=CronTrigger(hour=1, minute=0),
            id="daily_keywords_update",
            name="Daily Keywords Update",
            replace_existing=True
        )
        
        # Maintenance at 01:30
        scheduler.add_job(
            scheduled_maintenance,
            trigger=CronTrigger(hour=1, minute=30),
            id="daily_maintenance",
            name="Daily Maintenance Cleanup",
            replace_existing=True
        )
        
        # Optional: Stats update every 15 minutes for realtime dashboard
        scheduler.add_job(
            scheduled_stats_update,
            trigger=IntervalTrigger(minutes=15),
            id="periodic_stats_update",
            name="Periodic Stats Update (15min)",
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("📅 Scheduler started with daily jobs configured")
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {e}")
    
    logger.info("✅ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    # Stop Scheduler
    try:
        scheduler.shutdown(wait=False)
        logger.info("📅 Scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")
    
    # Disconnect from MongoDB
    await Database.disconnect()
    
    # Disconnect from Redis
    try:
        from mongodb.api.services.redis_service import RedisService
        await RedisService.disconnect()
    except:
        pass
    
    logger.info("👋 Application shutdown complete")


# ============================================
# Create FastAPI App
# ============================================

app = FastAPI(
    title=settings.app_name,
    description="""
    ## Disaster News Monitor API
    
    Real-time monitoring system for disaster-related news in Vietnam.
    
    ### Features:
    - 📰 Crawl and analyze disaster news from multiple sources
    - 🔍 NLP-based classification and severity detection
    - 📊 Real-time statistics and dashboard
    - 🔔 WebSocket for live updates
    - 🔐 JWT authentication
    
    ### Architecture:
    ```
    Crawler (RSS / Google News)
           ↓
       Normalizer
           ↓
    NLP Classifier (rule + ML)
           ↓
        MongoDB
           ↓
        FastAPI
           ↓
    Dashboard + WebSocket
    ```
    """,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# ============================================
# Middleware
# ============================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Rate Limiting
setup_rate_limiting(app)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and log requests"""
    start_time = time.time()
    
    # Handle CORS preflight - return 200 for OPTIONS
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    # Log request (skip health checks and static files)
    if not request.url.path.startswith(("/health", "/favicon", "/static")):
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)"
        )
    
    return response


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


# ============================================
# Include Routers
# ============================================

# Public routes
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(articles.router, prefix="/api/v1/articles", tags=["Articles"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["Sources"])
app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["Keywords"])
app.include_router(regions.router, prefix="/api/v1/regions", tags=["Regions"])

# Authentication routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Realtime routes - both prefixes for flexibility
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["Realtime"])
app.include_router(realtime.router, prefix="/realtime", tags=["Realtime WebSocket"])

# Internal/Admin routes (protected)
app.include_router(internal.router, prefix="/api/v1/internal", tags=["Internal"])

# Crawl routes
app.include_router(crawl_router.router, tags=["Crawl"])


# ============================================
# Root Endpoints
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled in production",
        "api_base": "/api/v1"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "scheduler_running": scheduler.running
    }


# ============================================
# Scheduler Management Endpoints
# ============================================

@app.get("/api/v1/scheduler/status", tags=["Scheduler"])
async def get_scheduler_status():
    """Get scheduler status and scheduled jobs"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "total_jobs": len(jobs)
    }


@app.post("/api/v1/scheduler/run/{job_id}", tags=["Scheduler"])
async def run_job_now(job_id: str, background_tasks: BackgroundTasks):
    """Manually trigger a scheduled job"""
    job_map = {
        "health_check": scheduled_health_check,
        "stats_update": scheduled_stats_update,
        "keywords_update": scheduled_keywords_update,
        "maintenance": scheduled_maintenance,
    }
    
    if job_id not in job_map:
        return {"error": f"Unknown job: {job_id}", "available_jobs": list(job_map.keys())}
    
    background_tasks.add_task(job_map[job_id])
    return {
        "success": True,
        "message": f"Job '{job_id}' started in background"
    }


@app.post("/api/v1/scheduler/run-all", tags=["Scheduler"])
async def run_all_jobs(background_tasks: BackgroundTasks):
    """Run all scheduled jobs in sequence"""
    background_tasks.add_task(scheduled_health_check)
    background_tasks.add_task(scheduled_stats_update)
    background_tasks.add_task(scheduled_keywords_update)
    background_tasks.add_task(scheduled_maintenance)
    
    return {
        "success": True,
        "message": "All jobs started in background"
    }


@app.post("/api/v1/scheduler/pause", tags=["Scheduler"])
async def pause_scheduler():
    """Pause the scheduler"""
    scheduler.pause()
    return {"success": True, "message": "Scheduler paused"}


@app.post("/api/v1/scheduler/resume", tags=["Scheduler"])
async def resume_scheduler():
    """Resume the scheduler"""
    scheduler.resume()
    return {"success": True, "message": "Scheduler resumed"}


# ============================================
# Run Application
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "mongodb.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    )