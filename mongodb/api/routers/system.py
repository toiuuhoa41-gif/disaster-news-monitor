from fastapi import APIRouter, Depends
from datetime import datetime
from mongodb.api.schemas.system import SystemStatus, RealtimeStats
from mongodb.api.services.stats_service import StatsService

router = APIRouter()


def get_stats_service():
    """Dependency injection for StatsService"""
    return StatsService()


@router.get("/status", response_model=SystemStatus)
async def get_system_status(stats_service: StatsService = Depends(get_stats_service)):
    return {
        "system_status": "running",
        "realtime_ingestion": True,
        "active_sources": await stats_service.get_active_sources_count(),
        "total_sources": await stats_service.get_total_sources_count(),
        "version": "1.0.0",
        "server_time": datetime.now().isoformat()
    }

@router.get("/realtime-stats", response_model=RealtimeStats)
async def get_realtime_stats(stats_service: StatsService = Depends(get_stats_service)):
    stats = await stats_service.get_realtime_stats()
    return stats