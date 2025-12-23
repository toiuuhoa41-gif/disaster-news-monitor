"""
Daily Scheduler API for Disaster News Monitor
Provides endpoints for automated daily data updates
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import logging
import asyncio
from datetime import datetime

# Import services
from mongodb.api.services.crawl_service import DailyCrawlService
from mongodb.api.services.stats_service import StatsUpdateService
from mongodb.api.services.maintenance_service import MaintenanceService
from mongodb.api.services.sources_service import SourcesHealthService
from mongodb.api.services.keywords_service import KeywordsUpdateService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Disaster Monitor Daily Scheduler",
    description="API for automated daily data updates and maintenance",
    version="1.0.0"
)

# Configure APScheduler
jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': AsyncIOExecutor()
}
job_defaults = {
    'coalesce': False,
    'max_instances': 1,
    'misfire_grace_time': 30
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='Asia/Ho_Chi_Minh'
)

@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup"""
    try:
        # Start the scheduler
        scheduler.start()
        logger.info("🚀 Scheduler started successfully")

        # Schedule daily jobs
        await schedule_daily_jobs()

    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler on app shutdown"""
    try:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Scheduler shut down")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")

async def schedule_daily_jobs():
    """Schedule all daily jobs"""
    try:
        # Health check sources at 0:00
        scheduler.add_job(
            daily_health_check,
            trigger=CronTrigger(hour=0, minute=0),
            id="daily_health_check",
            name="Daily Sources Health Check",
            replace_existing=True
        )

        # Crawl data at 0:05
        scheduler.add_job(
            daily_crawl,
            trigger=CronTrigger(hour=0, minute=5),
            id="daily_crawl",
            name="Daily Data Crawl",
            replace_existing=True
        )

        # Update stats at 0:30
        scheduler.add_job(
            daily_stats_update,
            trigger=CronTrigger(hour=0, minute=30),
            id="daily_stats_update",
            name="Daily Statistics Update",
            replace_existing=True
        )

        # Update keywords at 1:00
        scheduler.add_job(
            daily_keywords_update,
            trigger=CronTrigger(hour=1, minute=0),
            id="daily_keywords_update",
            name="Daily Keywords Update",
            replace_existing=True
        )

        # Maintenance cleanup at 1:30
        scheduler.add_job(
            daily_maintenance,
            trigger=CronTrigger(hour=1, minute=30),
            id="daily_maintenance",
            name="Daily Maintenance Cleanup",
            replace_existing=True
        )

        logger.info("📅 Daily jobs scheduled successfully")

    except Exception as e:
        logger.error(f"❌ Failed to schedule daily jobs: {e}")

# Daily job functions
async def daily_health_check():
    """Daily sources health check"""
    try:
        logger.info("🏥 Running daily health check...")
        service = SourcesHealthService()
        result = await service.check_all_sources()
        logger.info(f"✅ Health check completed: {result}")
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")

async def daily_crawl():
    """Daily data crawl"""
    try:
        logger.info("🌐 Running daily crawl...")
        service = DailyCrawlService()
        result = await service.crawl_all_sources()
        logger.info(f"✅ Daily crawl completed: {result}")
    except Exception as e:
        logger.error(f"❌ Daily crawl failed: {e}")

async def daily_stats_update():
    """Daily statistics update"""
    try:
        logger.info("📊 Running daily stats update...")
        service = StatsUpdateService()
        result = await service.update_daily_stats()
        logger.info(f"✅ Stats update completed: {result}")
    except Exception as e:
        logger.error(f"❌ Stats update failed: {e}")

async def daily_keywords_update():
    """Daily keywords update"""
    try:
        logger.info("🔍 Running daily keywords update...")
        service = KeywordsUpdateService()
        result = await service.update_keywords()
        logger.info(f"✅ Keywords update completed: {result}")
    except Exception as e:
        logger.error(f"❌ Keywords update failed: {e}")

async def daily_maintenance():
    """Daily maintenance cleanup"""
    try:
        logger.info("🧹 Running daily maintenance...")
        service = MaintenanceService()
        result = await service.daily_cleanup()
        logger.info(f"✅ Maintenance completed: {result}")
    except Exception as e:
        logger.error(f"❌ Maintenance failed: {e}")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Disaster Monitor Daily Scheduler API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler_running": scheduler.running
    }

@app.post("/api/crawl/daily")
async def trigger_daily_crawl(background_tasks: BackgroundTasks):
    """Manually trigger daily crawl"""
    try:
        background_tasks.add_task(daily_crawl)
        return {
            "success": True,
            "message": "Daily crawl started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stats/daily-update")
async def trigger_stats_update(background_tasks: BackgroundTasks):
    """Manually trigger stats update"""
    try:
        background_tasks.add_task(daily_stats_update)
        return {
            "success": True,
            "message": "Stats update started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/maintenance/cleanup")
async def trigger_maintenance(background_tasks: BackgroundTasks):
    """Manually trigger maintenance cleanup"""
    try:
        background_tasks.add_task(daily_maintenance)
        return {
            "success": True,
            "message": "Maintenance cleanup started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sources/health-check")
async def trigger_health_check(background_tasks: BackgroundTasks):
    """Manually trigger sources health check"""
    try:
        background_tasks.add_task(daily_health_check)
        return {
            "success": True,
            "message": "Health check started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/keywords/update")
async def trigger_keywords_update(background_tasks: BackgroundTasks):
    """Manually trigger keywords update"""
    try:
        background_tasks.add_task(daily_keywords_update)
        return {
            "success": True,
            "message": "Keywords update started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/run-all")
async def run_all_daily_tasks(background_tasks: BackgroundTasks):
    """Run all daily tasks in sequence"""
    try:
        # Run in sequence with delays
        background_tasks.add_task(daily_health_check)
        await asyncio.sleep(1)  # Small delay

        background_tasks.add_task(daily_crawl)
        await asyncio.sleep(1)

        background_tasks.add_task(daily_stats_update)
        await asyncio.sleep(1)

        background_tasks.add_task(daily_keywords_update)
        await asyncio.sleep(1)

        background_tasks.add_task(daily_maintenance)

        return {
            "success": True,
            "message": "All daily tasks started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scheduler/jobs")
async def get_scheduled_jobs():
    """Get list of scheduled jobs"""
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "success": True,
            "jobs": jobs,
            "total_jobs": len(jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/pause")
async def pause_scheduler():
    """Pause the scheduler"""
    try:
        scheduler.pause()
        return {
            "success": True,
            "message": "Scheduler paused",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/resume")
async def resume_scheduler():
    """Resume the scheduler"""
    try:
        scheduler.resume()
        return {
            "success": True,
            "message": "Scheduler resumed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get current dashboard statistics"""
    try:
        # This would typically fetch from the daily_stats collection
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Dashboard stats endpoint - implement service call",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "daily_scheduler:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )